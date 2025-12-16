"""Agent loader using Midori AI Agent Framework.

This module provides functions to load and validate agents using the Midori AI Agent
Framework, supporting multiple backends (OpenAI, HuggingFace, etc.).
"""
from __future__ import annotations

import os
from typing import TYPE_CHECKING

from .torch_checker import is_torch_available

if TYPE_CHECKING:
    from midori_ai_agent_base import MidoriAiAgentProtocol

# Import agent framework dependencies
try:
    from midori_ai_agent_base import (
        get_agent,
        get_agent_from_config,
        load_agent_config,
    )
    from midori_ai_logger import get_logger

    if TYPE_CHECKING:
        from midori_ai_agent_base import AgentConfig

    _AGENT_FRAMEWORK_AVAILABLE = True
except ImportError:
    get_agent = None
    get_agent_from_config = None
    load_agent_config = None
    get_logger = None
    _AGENT_FRAMEWORK_AVAILABLE = False

# Fallback to standard logging if midori_ai_logger not available
if _AGENT_FRAMEWORK_AVAILABLE:
    log = get_logger(__name__)
else:
    import logging

    log = logging.getLogger(__name__)


def find_config_file() -> Path | None:
    """Find config.toml in backend directory or parent directories.

    Returns:
        Path to config.toml if found, None otherwise
    """
    from pathlib import Path

    # Start from backend directory
    current = Path(__file__).parent.parent

    # Search upward for config.toml
    for _ in range(5):  # Max 5 levels up
        config_path = current / "config.toml"
        if config_path.exists():
            return config_path
        current = current.parent

    return None


async def load_agent(
    backend: str | None = None,
    model: str | None = None,
    validate: bool = True,
    use_config: bool = True,
) -> MidoriAiAgentProtocol:
    """Load an agent using the Midori AI Agent Framework.

    Primary backend: OpenAI agents (for OpenAI API, Ollama, LocalAI, etc.)
    Fallback backend: HuggingFace agents (for local inference)

    Args:
        backend: Backend type ("openai" or "huggingface")
                 If None, auto-selects based on config or environment
        model: Model name to use
               If None, uses config or environment variable
        validate: Whether to validate the agent after loading
        use_config: Whether to try loading from config.toml

    Returns:
        Agent implementing MidoriAiAgentProtocol

    Raises:
        ImportError: If required libraries are not available
        ValueError: If configuration is invalid
    """
    if not _AGENT_FRAMEWORK_AVAILABLE:
        msg = "Agent framework is not available. Install with: uv sync --extra llm-cpu"
        raise ImportError(msg)

    # Try loading from config file first
    if use_config:
        config_path = find_config_file()
        if config_path:
            log.info(f"Loading agent from config: {config_path}")
            try:
                agent = await get_agent_from_config(
                    config_path=str(config_path),
                    backend=backend,  # Allow override
                    model=model,  # Allow override
                )
                if validate:
                    log.info(f"Agent loaded from config: {config_path}")
                return agent
            except Exception as e:
                log.warning(
                    f"Failed to load from config: {e}, falling back to env vars"
                )

    # Fall back to environment variables
    log.info("Loading agent from environment variables")

    # Auto-detect backend: prioritize OpenAI, fallback to HuggingFace
    if backend is None:
        openai_url = os.getenv("OPENAI_API_URL", "unset")
        if openai_url != "unset":
            backend = "openai"
        elif is_torch_available():
            backend = "huggingface"
            # Use recommended model for HuggingFace with high reasoning
            if model is None:
                model = "openai/gpt-oss-20b"
        else:
            msg = "No backend available. Set OPENAI_API_URL or install torch for local inference."
            raise ValueError(msg)

    # Get model from environment if not specified
    if model is None:
        model = os.getenv("AF_LLM_MODEL", "gpt-oss:20b")

    # Get API configuration (for OpenAI backend)
    api_key = os.getenv("OPENAI_API_KEY", "")
    base_url = os.getenv("OPENAI_API_URL")

    # Create agent using framework factory
    agent = await get_agent(
        backend=backend,
        model=model,
        api_key=api_key,
        base_url=base_url,
    )

    if validate:
        sanitized_backend = sanitize_log_str(backend) if backend else backend
        sanitized_model = sanitize_log_str(model) if model else model
        log.info(f"Agent loaded: backend={sanitized_backend}, model={sanitized_model}")

    return agent


def sanitize_log_str(value: str) -> str:
    """
    Sanitize a string for logging by removing line breaks and carriage return characters
    and making control characters explicit for audit log clarity.
    """
    if not isinstance(value, str):
        value = str(value)
    # Remove \r and \n, and optionally other non-printable control characters
    return value.replace('\r', '').replace('\n', '')

def get_agent_config() -> AgentConfig | None:
    """Get current agent configuration from file.

    Returns:
        AgentConfig if config file exists, None otherwise
    """
    config_path = find_config_file()
    if config_path:
        if load_agent_config is None:
            return None
            
        try:
            return load_agent_config(config_path=str(config_path))
        except Exception as e:
            log.error(f"Failed to load config: {e}")
            return None
    return None


async def validate_agent(agent: MidoriAiAgentProtocol) -> bool:
    """Validate that an agent is working correctly.

    Sends a test prompt and checks if the response is longer than 5 characters,
    indicating the model can reason and generate meaningful content.

    Args:
        agent: The agent to validate

    Returns:
        True if validation passes, False otherwise
    """
    if not _AGENT_FRAMEWORK_AVAILABLE:
        msg = "Agent framework is not available. Install with: uv sync --extra llm-cpu"
        raise ImportError(msg)

    from midori_ai_agent_base import AgentPayload

    try:
        test_payload = AgentPayload(
            user_message="Please say 'Hello world' and 5 words about yourself",
            thinking_blob="",
            system_context="You are a helpful assistant.",
            user_profile={},
            tools_available=[],
            session_id="validation",
        )

        response = await agent.invoke(test_payload)

        # Check if response is longer than 5 characters
        if len(response.response) > 5:
            log.info(
                f"Agent validation passed. Response length: {len(response.response)}"
            )
            return True
        else:
            log.warning(
                f"Agent validation failed. Response too short: {response.response}"
            )
            return False
    except Exception as e:
        log.error(f"Agent validation failed with error: {e}")
        return False


__all__ = ["load_agent", "get_agent_config", "find_config_file", "validate_agent"]
