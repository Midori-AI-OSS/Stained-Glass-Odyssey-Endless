import asyncio
from collections.abc import AsyncIterator
from enum import Enum
import os
from typing import Protocol

from .torch_checker import is_torch_available
from .torch_checker import require_torch

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

# Import OpenAI independently of torch
try:
    from openai import AsyncOpenAI
    _OPENAI_AVAILABLE = True
except ImportError:
    AsyncOpenAI = None
    _OPENAI_AVAILABLE = False

from .safety import ensure_ram
from .safety import gguf_strategy
from .safety import model_memory_requirements
from .safety import pick_device


class SupportsStream(Protocol):
    async def generate_stream(self, text: str) -> AsyncIterator[str]:
        ...


class ModelName(str, Enum):
    DEEPSEEK = "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"
    GEMMA = "google/gemma-3-4b-it"
    GGUF = "gguf"
    REMOTE_OPENAI = "remote-openai"


class _LangChainWrapper:
    def __init__(self, llm) -> None:
        self._llm = llm

    async def generate_stream(self, text: str) -> AsyncIterator[str]:
        result = await asyncio.to_thread(self._llm.invoke, text)
        yield result


class _OpenAIRemoteWrapper:
    """Wrapper for remote OpenAI-compatible API with reasoning support."""

    def __init__(self, client: "AsyncOpenAI", model: str = "gpt-oss:20b") -> None:
        self._client = client
        self._model = model

    async def generate_stream(self, text: str) -> AsyncIterator[str]:
        """Stream response from remote OpenAI API with reasoning effort."""
        # Use high reasoning effort as specified in requirements
        try:
            stream = await self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": text}],
                stream=True,
                reasoning_effort="high",
                temperature=0.7,
            )
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except TypeError:
            # Fallback if reasoning_effort is not supported by this API
            stream = await self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": text}],
                stream=True,
                temperature=0.7,
            )
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content


def load_llm(model: str | None = None, *, gguf_path: str | None = None) -> SupportsStream:
    # Check for remote OpenAI configuration first
    openai_url = os.getenv("OPENAI_API_URL", "unset")
    openai_key = os.getenv("OPENAI_API_KEY", "unset")

    # If remote OpenAI is configured, use it
    if openai_url != "unset" and openai_key != "unset":
        if not _OPENAI_AVAILABLE:
            msg = "OpenAI library is not available. Install with: uv pip install openai"
            raise ImportError(msg)

        # Use the specified model or default to gpt-oss:20b
        remote_model = model or os.getenv("AF_LLM_MODEL", "gpt-oss:20b")
        client = AsyncOpenAI(base_url=openai_url, api_key=openai_key)
        return _OpenAIRemoteWrapper(client, remote_model)

    # Fall back to local models (requires torch)
    require_torch()
    name = model or os.getenv("AF_LLM_MODEL", ModelName.DEEPSEEK.value)
    if name == ModelName.DEEPSEEK.value:
        min_ram, _ = model_memory_requirements(name)
        ensure_ram(min_ram)
        device = pick_device()
        # Configure generation parameters to avoid warnings
        model_kwargs = {
            "max_new_tokens": 512,
            "do_sample": True,
            "temperature": 0.7,
            "pad_token_id": 50256,  # Common pad token ID
        }
        if device == 0:
            pipe = pipeline(
                "text-generation",
                model=ModelName.DEEPSEEK.value,
                device_map="auto",
                model_kwargs=model_kwargs,
            )
        else:
            pipe = pipeline(
                "text-generation",
                model=ModelName.DEEPSEEK.value,
                device=device,
                model_kwargs=model_kwargs,
            )
        return _LangChainWrapper(HuggingFacePipeline(pipeline=pipe))
    if name == ModelName.GEMMA.value:
        min_ram, _ = model_memory_requirements(name)
        ensure_ram(min_ram)
        device = pick_device()
        # Configure generation parameters to avoid warnings
        model_kwargs = {
            "max_new_tokens": 512,
            "do_sample": True,
            "temperature": 0.7,
            "pad_token_id": 50256,  # Common pad token ID
        }
        if device == 0:
            pipe = pipeline(
                "text-generation",
                model=ModelName.GEMMA.value,
                device_map="auto",
                model_kwargs=model_kwargs,
            )
        else:
            pipe = pipeline(
                "text-generation",
                model=ModelName.GEMMA.value,
                device=device,
                model_kwargs=model_kwargs,
            )
        return _LangChainWrapper(HuggingFacePipeline(pipeline=pipe))
    if name == ModelName.GGUF.value:
        path = gguf_path or os.getenv("AF_GGUF_PATH")
        if path is None:
            msg = "GGUF model path must be provided via argument or AF_GGUF_PATH"
            raise ValueError(msg)
        kwargs = gguf_strategy(path)
        return _LangChainWrapper(LlamaCpp(model_path=path, **kwargs))
    msg = f"Unsupported model: {name}"
    raise ValueError(msg)


__all__ = ["ModelName", "SupportsStream", "load_llm"]
