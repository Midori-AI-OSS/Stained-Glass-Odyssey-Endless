# Migrate LLM Loader to Agent Framework

## Task ID
`32e92203-migrate-llm-loader`

## Priority
High

## Status
WIP

## Description
Replace the custom `backend/llms/loader.py` module with the Midori AI Agent Framework's standardized agent interface. This eliminates custom wrappers and protocols in favor of the framework's `MidoriAiAgentProtocol`, `AgentPayload`, and `AgentResponse`.

## Context
Currently, `backend/llms/loader.py` implements:
- Custom `SupportsStream` protocol
- `_LangChainWrapper` for HuggingFace models
- `_OpenAIAgentsWrapper` for remote OpenAI APIs
- Manual model loading logic
- Custom validation functions
- `load_llm()` function that returns wrapper objects

The Agent Framework provides:
- `MidoriAiAgentProtocol` standard interface
- Pre-built adapters (OpenAIAgentsAdapter, HuggingFaceLocalAgent, LangChainAdapter)
- `get_agent()` factory function
- `AgentPayload` and `AgentResponse` standard models

## Rationale
- **Less Code**: Remove ~250 lines of custom wrapper code
- **Standardization**: Use framework's proven interfaces
- **Better Features**: Get streaming, tools, memory support built-in
- **Easier Testing**: Framework includes test utilities
- **Future-Proof**: New backends can be added via framework updates

## Objectives
1. Replace custom wrappers with framework adapters
2. Update `load_llm()` to use `get_agent()` factory
3. Replace `SupportsStream` protocol with `MidoriAiAgentProtocol`
4. Maintain backward compatibility during transition
5. Keep torch_checker.py and safety.py for system checks

## Implementation Steps

### Step 1: Understand Current Usage
Review how `load_llm()` is currently used:
```bash
cd backend
grep -rn "from llms.loader import" . --include="*.py" | grep -v ".venv"
grep -rn "load_llm(" . --include="*.py" | grep -v ".venv"
```

Document all call sites:
- `autofighter/rooms/chat.py` - Chat room
- `routes/config.py` - LRM testing endpoint
- Any other locations

### Step 2: Create New Agent Loader
Create `backend/llms/agent_loader.py`:

```python
"""Agent loader using Midori AI Agent Framework."""
from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

from midori_ai_agent_base import MidoriAiAgentProtocol, get_agent

if TYPE_CHECKING:
    from midori_ai_agent_base import AgentPayload, AgentResponse

from .torch_checker import is_torch_available

log = logging.getLogger(__name__)


async def load_agent(
    backend: str | None = None,
    model: str | None = None,
    validate: bool = True,
) -> MidoriAiAgentProtocol:
    """Load an agent using the Midori AI Agent Framework.
    
    Args:
        backend: Backend type ("openai", "huggingface", "langchain")
                 If None, auto-selects based on environment
        model: Model name to use
               If None, uses environment variable or default
        validate: Whether to validate the agent (future use)
    
    Returns:
        Agent implementing MidoriAiAgentProtocol
    
    Raises:
        ImportError: If required libraries are not available
        ValueError: If configuration is invalid
    """
    # Auto-detect backend based on environment
    if backend is None:
        openai_url = os.getenv("OPENAI_API_URL", "unset")
        if openai_url != "unset":
            backend = "openai"
        elif is_torch_available():
            backend = "huggingface"
        else:
            backend = "langchain"
    
    # Get model from environment if not specified
    if model is None:
        model = os.getenv("AF_LLM_MODEL", "gpt-oss:20b")
    
    # Get API configuration
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
    
    Args:
        agent: The agent to validate
    
    Returns:
        True if validation passes, False otherwise
    """
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
```

### Step 3: Create Compatibility Layer
Create `backend/llms/compat.py` for backward compatibility:

```python
"""Backward compatibility layer for old loader interface."""
from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import Protocol

from midori_ai_agent_base import AgentPayload, MidoriAiAgentProtocol

from .agent_loader import load_agent as _load_agent


class SupportsStream(Protocol):
    """Legacy protocol for streaming interface."""
    
    async def generate_stream(self, text: str) -> AsyncIterator[str]:
        """Generate streaming response from text."""
        ...


class _AgentStreamWrapper:
    """Wrapper to provide old streaming interface for new agents."""
    
    def __init__(self, agent: MidoriAiAgentProtocol) -> None:
        self._agent = agent
    
    async def generate_stream(self, text: str) -> AsyncIterator[str]:
        """Generate streaming response using agent framework.
        
        Args:
            text: Input text (treated as user message)
        
        Yields:
            Response chunks
        """
        # Create payload from text
        payload = AgentPayload(
            user_message=text,
            thinking_blob="",
            system_context="You are a helpful AI assistant.",
            user_profile={},
            tools_available=[],
            session_id="legacy",
        )
        
        # Check if agent supports streaming
        if await self._agent.supports_streaming():
            # Stream from agent
            async for chunk in self._agent.stream(payload):
                yield chunk
        else:
            # Fall back to non-streaming
            response = await self._agent.invoke(payload)
            yield response.response


def load_llm(
    model: str | None = None,
    *,
    gguf_path: str | None = None,
    validate: bool = True,
) -> SupportsStream:
    """Legacy function for loading LLM with old interface.
    
    This is a compatibility shim. New code should use load_agent() instead.
    
    Args:
        model: Model name
        gguf_path: Path to GGUF file (deprecated, use config instead)
        validate: Whether to validate
    
    Returns:
        Object with generate_stream method
    """
    # Run async load_agent in sync context
    agent = asyncio.run(_load_agent(model=model, validate=validate))
    return _AgentStreamWrapper(agent)


__all__ = ["load_llm", "SupportsStream"]
```

### Step 4: Update llms/__init__.py
Update `backend/llms/__init__.py`:

```python
"""LLM and agent loading utilities."""

# New agent framework interface (preferred)
from .agent_loader import load_agent
from .agent_loader import validate_agent

# Legacy compatibility interface
from .compat import SupportsStream
from .compat import load_llm

# Keep existing utilities
from .torch_checker import is_torch_available
from .torch_checker import require_torch

__all__ = [
    # New interface
    "load_agent",
    "validate_agent",
    # Legacy interface
    "load_llm",
    "SupportsStream",
    # Utilities
    "is_torch_available",
    "require_torch",
]
```

### Step 5: Update ModelName Enum
The old `ModelName` enum may need updating. Consider:

Option A: Keep it but mark as deprecated
```python
# In agent_loader.py or separate file
from enum import Enum

class ModelName(str, Enum):
    """Deprecated: Use model strings directly."""
    OPENAI_20B = "openai/gpt-oss-20b"
    OPENAI_120B = "openai/gpt-oss-120b"
    GGUF = "gguf"
    REMOTE_OPENAI = "remote-openai"
```

Option B: Remove it and update all references to use strings

Choose based on how widely it's used in the codebase.

### Step 6: Test the New Loader
Create test script `backend/test_agent_loader.py`:

```python
"""Test the new agent loader."""
import asyncio
import os

from llms.agent_loader import load_agent, validate_agent
from midori_ai_agent_base import AgentPayload


async def test_agent_loader():
    """Test loading and using an agent."""
    # Test with environment variables
    os.environ["OPENAI_API_URL"] = "http://localhost:11434/v1"
    os.environ["OPENAI_API_KEY"] = "not-needed"
    os.environ["AF_LLM_MODEL"] = "llama3:8b"
    
    print("Loading agent...")
    agent = await load_agent()
    
    print("Validating agent...")
    is_valid = await validate_agent(agent)
    print(f"Validation: {'PASSED' if is_valid else 'FAILED'}")
    
    print("\nTesting agent invoke...")
    payload = AgentPayload(
        user_message="What is 2+2?",
        thinking_blob="",
        system_context="You are a math tutor.",
        user_profile={},
        tools_available=[],
        session_id="test",
    )
    
    response = await agent.invoke(payload)
    print(f"Response: {response.response}")
    
    print("\nTesting streaming...")
    if await agent.supports_streaming():
        print("Streaming: ", end="", flush=True)
        async for chunk in agent.stream(payload):
            print(chunk, end="", flush=True)
        print()
    else:
        print("Streaming not supported")


if __name__ == "__main__":
    asyncio.run(test_agent_loader())
```

Run test:
```bash
cd backend
uv run python test_agent_loader.py
```

### Step 7: Clean Up Old Code
Once new loader is working:
1. Archive old `loader.py` as `loader.py.bak`
2. Remove `_LangChainWrapper` class
3. Remove `_OpenAIAgentsWrapper` class
4. Remove old `load_llm` implementation
5. Keep `ModelName` if still used, otherwise remove

### Step 8: Update safety.py
Review `backend/llms/safety.py`:
- Keep functions that are still useful
- Remove functions that are now handled by framework
- Update imports if needed

## Acceptance Criteria
- [ ] New `agent_loader.py` created with `load_agent()` function
- [ ] Compatibility layer `compat.py` created for backward compatibility
- [ ] `llms/__init__.py` updated to export new and legacy interfaces
- [ ] Old `loader.py` archived or removed
- [ ] Test script validates new loader works
- [ ] All imports of `load_llm` still work (via compat layer)
- [ ] `ModelName` enum handled (kept or removed)
- [ ] `torch_checker.py` kept and functional
- [ ] `safety.py` updated or kept as-is
- [ ] Linting passes (`uv tool run ruff check backend --fix`)
- [ ] No breaking changes to existing code

## Testing Requirements

### Unit Tests
Create `backend/tests/test_agent_loader.py`:
```python
import pytest
from llms.agent_loader import load_agent, validate_agent
from midori_ai_agent_base import AgentPayload


@pytest.mark.asyncio
async def test_load_agent():
    """Test agent loading."""
    agent = await load_agent(backend="huggingface", model="TinyLlama/TinyLlama-1.1B-Chat-v1.0")
    assert agent is not None


@pytest.mark.asyncio
async def test_validate_agent():
    """Test agent validation."""
    agent = await load_agent(backend="huggingface", model="TinyLlama/TinyLlama-1.1B-Chat-v1.0")
    is_valid = await validate_agent(agent)
    assert is_valid is True


@pytest.mark.asyncio
async def test_agent_invoke():
    """Test agent invocation."""
    agent = await load_agent(backend="huggingface", model="TinyLlama/TinyLlama-1.1B-Chat-v1.0")
    payload = AgentPayload(
        user_message="Hello",
        thinking_blob="",
        system_context="You are helpful.",
        user_profile={},
        tools_available=[],
        session_id="test",
    )
    response = await agent.invoke(payload)
    assert len(response.response) > 0
```

### Compatibility Tests
Create `backend/tests/test_loader_compat.py`:
```python
from llms.compat import load_llm


def test_legacy_load_llm():
    """Test backward compatibility."""
    llm = load_llm(model="TinyLlama/TinyLlama-1.1B-Chat-v1.0")
    assert hasattr(llm, "generate_stream")
```

### Integration Tests
```bash
# Test with actual models (if time permits)
cd backend
uv run pytest tests/test_agent_loader.py -v
```

## Dependencies
- Requires: `12af34e9-update-dependencies.md` (must be completed first)
- Blocks: `c0f04e25-update-chat-room.md`
- Blocks: `96e5fdb9-update-config-routes.md`
- Related: `656b2a7e-create-config-support.md` (can be done in parallel)

## References
- [midori-ai-agent-base docs](https://github.com/Midori-AI-OSS/agents-packages/blob/main/midori-ai-agent-base/docs.md)
- [midori-ai-agent-openai docs](https://github.com/Midori-AI-OSS/agents-packages/blob/main/midori-ai-agent-openai/docs.md)
- [midori-ai-agent-huggingface docs](https://github.com/Midori-AI-OSS/agents-packages/blob/main/midori-ai-agent-huggingface/docs.md)
- Current: `backend/llms/loader.py`
- Current: `backend/llms/torch_checker.py`
- Current: `backend/llms/safety.py`

## Notes for Coder
- Keep backward compatibility via compat.py for smooth transition
- The framework's `get_agent()` handles backend selection automatically
- AgentPayload is more structured than the old text-only interface
- Consider keeping ModelName enum if it's widely used in config/routes
- The framework includes memory management - don't need custom implementation
- Streaming is built into the framework - simpler than custom implementation
- Tool support is available via `invoke_with_tools()` if needed in future
