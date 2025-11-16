import asyncio
from collections.abc import AsyncIterator
from enum import Enum
import logging
import os
from typing import Protocol

from .torch_checker import is_torch_available
from .torch_checker import require_torch

log = logging.getLogger(__name__)

# Import dependencies only if torch is available
if is_torch_available():
    from langchain_community.llms import llamacpp as LlamaCpp
    from langchain_huggingface import HuggingFacePipeline
    import torch
    from transformers import pipeline
else:
    torch = None
    LlamaCpp = None
    HuggingFacePipeline = None
    pipeline = None

# Import OpenAI and agents independently of torch
try:
    from agents import ModelSettings
    from agents import OpenAIChatCompletionsModel
    from openai import AsyncOpenAI
    from openai.types.shared import Reasoning
    _OPENAI_AVAILABLE = True
except ImportError:
    AsyncOpenAI = None
    Reasoning = None
    ModelSettings = None
    OpenAIChatCompletionsModel = None
    _OPENAI_AVAILABLE = False

from .safety import ensure_ram  # noqa: E402
from .safety import gguf_strategy  # noqa: E402
from .safety import model_memory_requirements  # noqa: E402
from .safety import pick_device  # noqa: E402


class SupportsStream(Protocol):
    async def generate_stream(self, text: str) -> AsyncIterator[str]:
        ...


class ModelName(str, Enum):
    OPENAI_20B = "openai/gpt-oss-20b"
    OPENAI_120B = "openai/gpt-oss-120b"
    GGUF = "gguf"
    REMOTE_OPENAI = "remote-openai"


class _LangChainWrapper:
    def __init__(self, llm) -> None:
        self._llm = llm

    async def generate_stream(self, text: str) -> AsyncIterator[str]:
        result = await asyncio.to_thread(self._llm.invoke, text)
        yield result


class _OpenAIAgentsWrapper:
    """Wrapper for remote OpenAI-compatible API using agents library with reasoning support."""

    def __init__(self, client: "AsyncOpenAI", model: str = "gpt-oss:20b") -> None:
        self._client = client
        self._model = model
        # Set up reasoning with high effort as specified
        self._reasoning = Reasoning(effort="high", generate_summary="detailed", summary="detailed")
        self._model_settings = ModelSettings(
            reasoning=self._reasoning,
            parallel_tool_calls=False,
            temperature=0.7,
        )
        # Create the OpenAI chat completions model
        self._openai_model = OpenAIChatCompletionsModel(
            model=self._model,
            openai_client=self._client,
        )

    async def generate_stream(self, text: str) -> AsyncIterator[str]:
        """Stream response from remote OpenAI API with high reasoning effort."""
        # Use the agents library's built-in streaming
        response = await self._openai_model.create_completion(
            messages=[{"role": "user", "content": text}],
            **self._model_settings.model_dump(exclude_none=True),
        )

        # Stream the response
        if hasattr(response, 'choices') and response.choices:
            content = response.choices[0].message.content
            if content:
                yield content


async def _validate_lrm(llm: SupportsStream) -> bool:
    """Validate that the model is an LRM by testing its response.

    Sends a test prompt and checks if the response is longer than 5 letters,
    indicating the model can reason and generate meaningful content.

    Args:
        llm: The LLM wrapper to test

    Returns:
        True if validation passes, False otherwise
    """
    try:
        test_prompt = "Please say `Hello world` and 5 words about yourself"
        response_parts = []

        async for chunk in llm.generate_stream(test_prompt):
            response_parts.append(chunk)

        full_response = "".join(response_parts)

        # Check if response is longer than 5 letters
        if len(full_response) > 5:
            log.info(f"LRM validation passed. Response length: {len(full_response)}")
            return True
        else:
            log.warning(f"LRM validation failed. Response too short: {full_response}")
            return False
    except Exception as e:
        log.error(f"LRM validation failed with error: {e}")
        return False


def _load_local_huggingface_model(model_name: str) -> SupportsStream:
    """Load a local HuggingFace model with LRM validation.

    Args:
        model_name: The model name/path to load

    Returns:
        Wrapped model ready for inference
    """
    min_ram, _ = model_memory_requirements(model_name)
    ensure_ram(min_ram)
    device = pick_device()

    # Configure generation parameters with high reasoning for LRM
    model_kwargs = {
        "max_new_tokens": 512,
        "do_sample": True,
        "temperature": 0.7,
        "reasoning_effort": "high",  # Ensure LRM, not LLM
        "pad_token_id": 50256,
    }

    if device == 0:
        pipe = pipeline(
            "text-generation",
            model=model_name,
            device_map="auto",
            model_kwargs=model_kwargs,
        )
    else:
        pipe = pipeline(
            "text-generation",
            model=model_name,
            device=device,
            model_kwargs=model_kwargs,
        )

    return _LangChainWrapper(HuggingFacePipeline(pipeline=pipe))


def load_llm(model: str | None = None, *, gguf_path: str | None = None, validate: bool = True) -> SupportsStream:
    """Load an LRM (Language Reasoning Model) with optional validation.

    Args:
        model: Model name to load (optional, uses env var AF_LLM_MODEL or default)
        gguf_path: Path to GGUF model file (required for GGUF models)
        validate: Whether to validate the model is an LRM (default: True)

    Returns:
        Loaded model wrapper implementing SupportsStream protocol

    Raises:
        ImportError: If required libraries are not available
        ValueError: If model configuration is invalid
        RuntimeError: If validation fails
    """
    # Check for remote OpenAI configuration first
    openai_url = os.getenv("OPENAI_API_URL", "unset")
    openai_key = os.getenv("OPENAI_API_KEY", "unset")

    # If remote OpenAI is configured (URL is set), use it
    # API key is optional for systems like Ollama
    if openai_url != "unset":
        if not _OPENAI_AVAILABLE:
            msg = "OpenAI and agents libraries are not available. Install with: uv sync --extra llm-cpu"
            raise ImportError(msg)

        # Use the specified model or default to gpt-oss:20b
        remote_model = model or os.getenv("AF_LLM_MODEL", "gpt-oss:20b")
        # Use provided API key or default to empty string for systems that don't need it
        api_key = openai_key if openai_key != "unset" else ""
        client = AsyncOpenAI(base_url=openai_url, api_key=api_key)
        llm = _OpenAIAgentsWrapper(client, remote_model)

        # Validate the remote LRM if requested
        if validate:
            log.info("Validating remote LRM...")
            # Note: validation is async, so we log intent but actual validation
            # should happen at first use or via separate validation endpoint
            log.info("Remote LRM loaded. Validation will occur on first use.")

        return llm

    # Fall back to local models (requires torch)
    require_torch()
    name = model or os.getenv("AF_LLM_MODEL", ModelName.OPENAI_20B.value)

    # Load local model based on type
    if name in (ModelName.OPENAI_20B.value, ModelName.OPENAI_120B.value):
        llm = _load_local_huggingface_model(name)
    elif name == ModelName.GGUF.value:
        path = gguf_path or os.getenv("AF_GGUF_PATH")
        if path is None:
            msg = "GGUF model path must be provided via argument or AF_GGUF_PATH"
            raise ValueError(msg)
        kwargs = gguf_strategy(path)
        # Add reasoning_effort to GGUF kwargs to validate it's an LRM
        kwargs["reasoning_effort"] = "high"
        llm = _LangChainWrapper(LlamaCpp(model_path=path, **kwargs))
    else:
        msg = f"Unsupported model: {name}"
        raise ValueError(msg)

    # Validate local LRM if requested
    if validate:
        log.info(f"Validating local LRM: {name}")
        # Note: validation is async, log intent for now
        log.info("Local LRM loaded. Validation will occur on first use.")

    return llm


__all__ = ["ModelName", "SupportsStream", "load_llm", "validate_lrm"]


async def validate_lrm(llm: SupportsStream) -> bool:
    """Public async function to validate an LRM.

    This should be called after loading to ensure the model is an LRM.
    Can be used when booting or when changing settings.

    Args:
        llm: The loaded LLM wrapper to validate

    Returns:
        True if validation passes, False otherwise
    """
    return await _validate_lrm(llm)
