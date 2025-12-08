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
    from midori_ai_agent_base import get_agent
    from midori_ai_logger import get_logger

    _AGENT_FRAMEWORK_AVAILABLE = True
except ImportError:
    get_agent = None
    get_logger = None
    _AGENT_FRAMEWORK_AVAILABLE = False

# Fallback to standard logging if midori_ai_logger not available
if _AGENT_FRAMEWORK_AVAILABLE:
    log = get_logger(__name__)
else:
    import logging

    log = logging.getLogger(__name__)


async def load_agent(
    backend: str | None = None,
    model: str | None = None,
    validate: bool = True,
) -> MidoriAiAgentProtocol:
    """Load an agent using the Midori AI Agent Framework.

    Primary backend: OpenAI agents (for OpenAI API, Ollama, LocalAI, etc.)
    Fallback backend: HuggingFace agents (for local inference)

    Args:
        backend: Backend type ("openai" or "huggingface")
                 If None, auto-selects: openai if URL set, else huggingface if torch available
        model: Model name to use
               If None, uses environment variable or default
        validate: Whether to validate the agent after loading

    Returns:
        Agent implementing MidoriAiAgentProtocol

    Raises:
        ImportError: If required libraries are not available
        ValueError: If configuration is invalid
    """
    if not _AGENT_FRAMEWORK_AVAILABLE:
        msg = "Agent framework is not available. Install with: uv sync --extra llm-cpu"
        raise ImportError(msg)

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
        log.info(f"Agent loaded: backend={backend}, model={model}")

    return agent


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
            log.info(f"Agent validation passed. Response length: {len(response.response)}")
            return True
        else:
            log.warning(f"Agent validation failed. Response too short: {response.response}")
            return False
    except Exception as e:
        log.error(f"Agent validation failed with error: {e}")
        return False


__all__ = ["load_agent", "validate_agent"]
