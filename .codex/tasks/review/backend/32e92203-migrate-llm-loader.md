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
- **Breaking Changes**: Intentionally break old code to find issues faster

## Objectives
1. Replace custom wrappers with framework adapters
2. Replace `load_llm()` with `load_agent()` using `get_agent()` factory
3. Replace `SupportsStream` protocol with `MidoriAiAgentProtocol`
4. **BREAK backward compatibility** - remove all old code and compatibility layers
5. Remove GGUF support (not needed with agent framework)
6. Keep torch_checker.py for system checks, verify safety.py works with agents
7. Focus on OpenAI agents (primary) and HuggingFace agents (fallback)

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

import os
from typing import TYPE_CHECKING

from midori_ai_agent_base import MidoriAiAgentProtocol, get_agent
from midori_ai_logger import get_logger

if TYPE_CHECKING:
    from midori_ai_agent_base import AgentPayload, AgentResponse

from .torch_checker import is_torch_available

log = get_logger(__name__)


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
        validate: Whether to validate the agent (future use)
    
    Returns:
        Agent implementing MidoriAiAgentProtocol
    
    Raises:
        ImportError: If required libraries are not available
        ValueError: If configuration is invalid
    """
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
            raise ValueError("No backend available. Set OPENAI_API_URL or install torch for local inference.")
    
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

### Step 3: Update llms/__init__.py (NO Compatibility Layer)
Update `backend/llms/__init__.py` to export ONLY new interfaces:

```python
"""LLM and agent loading utilities - NEW AGENT FRAMEWORK ONLY."""

# New agent framework interface (ONLY interface now)
from .agent_loader import load_agent
from .agent_loader import validate_agent

# Keep existing utilities
from .torch_checker import is_torch_available
from .torch_checker import require_torch

__all__ = [
    # New interface (breaking change - old code must update)
    "load_agent",
    "validate_agent",
    # Utilities
    "is_torch_available",
    "require_torch",
]

# OLD INTERFACES REMOVED:
# - load_llm() - REMOVED, use load_agent() instead
# - SupportsStream - REMOVED, use MidoriAiAgentProtocol instead
```

### Step 4: Remove Old loader.py
Delete or archive the old loader:
```bash
cd backend/llms
# Archive old loader for reference
mv loader.py loader.py.old.bak
# Or delete it entirely
# rm loader.py
```
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

### Step 5: Remove ModelName Enum (Breaking Change)
The old `ModelName` enum is removed. Update all code to use model strings directly:
- Old: `ModelName.OPENAI_20B.value`
- New: `"openai/gpt-oss-20b"`

**GGUF support is REMOVED** - not needed with agent framework.

Find and update all references:
```bash
cd backend
grep -rn "ModelName" . --include="*.py" | grep -v ".venv"
```

### Step 6: Verify safety.py Works with Agent Framework
Review `backend/llms/safety.py` to ensure functions work with Midori AI HuggingFace agents:
```bash
cd backend/llms
cat safety.py
```

Key functions to verify:
- `model_memory_requirements()` - Should work with HuggingFace model names
- `pick_device()` - Should work with agent framework device selection
- `gguf_strategy()` - **REMOVE** (GGUF support dropped)

Update or remove incompatible functions.

### Step 7: Test the New Loader
Create test script `backend/test_agent_loader.py`:

```python
"""Test the new agent loader."""
import asyncio
from midori_ai_agent_base import AgentPayload
from midori_ai_logger import get_logger
from llms.agent_loader import load_agent, validate_agent

log = get_logger(__name__)


async def test_agent_loader():
    """Test loading and using an agent."""
    # Test with HuggingFace backend (local, no external dependencies)
    log.info("Loading agent with HuggingFace backend...")
    agent = await load_agent(backend="huggingface", model="openai/gpt-oss-20b")
    
    log.info("Validating agent...")
    is_valid = await validate_agent(agent)
    log.info(f"Validation: {'PASSED' if is_valid else 'FAILED'}")
    
    log.info("Testing agent invoke...")
    payload = AgentPayload(
        user_message="What is 2+2?",
        thinking_blob="",
        system_context="You are a math tutor.",
        user_profile={},
        tools_available=[],
        session_id="test",
    )
    
    response = await agent.invoke(payload)
    log.info(f"Response: {response.response}")
    
    log.info("Testing streaming...")
    if await agent.supports_streaming():
        log.info("Streaming supported, testing...")
        async for chunk in agent.stream(payload):
            print(chunk, end="", flush=True)
        print()
    else:
        log.info("Streaming not supported")


if __name__ == "__main__":
    asyncio.run(test_agent_loader())
```

Run test:
```bash
cd backend
uv run python test_agent_loader.py
```

### Step 8: Clean Up Old Code (Breaking Change)
Delete old code completely:
```bash
cd backend/llms
# DELETE old loader
rm loader.py

# No compat.py needed - breaking change is intentional
```

All code using `load_llm()` must be updated to use `load_agent()`.

## Acceptance Criteria
- [ ] New `agent_loader.py` created with `load_agent()` function using midori_ai_logger
- [ ] **NO compatibility layer** - breaking changes intentional
- [ ] `llms/__init__.py` updated to export ONLY new interfaces
- [ ] Old `loader.py` DELETED
- [ ] Test script validates new loader works with HuggingFace backend
- [ ] `ModelName` enum REMOVED completely
- [ ] **GGUF support REMOVED**
- [ ] `torch_checker.py` kept and functional
- [ ] `safety.py` verified to work with agents or updated
- [ ] All old `load_llm()` calls must be manually updated (breaking change)
- [ ] Linting passes (`uv tool run ruff check backend --fix`)
- [ ] Intentional breaking changes documented

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

### Integration Tests
```bash
# Test with actual models
cd backend
uv run pytest tests/test_agent_loader.py -v
```

## Dependencies
- Requires: `12af34e9-update-dependencies.md` (must be completed first)
- Blocks: `c0f04e25-update-chat-room.md`
- Blocks: `96e5fdb9-update-config-routes.md`
- Blocks: `5e609bc6-webui-backend-selection.md` (new WebUI task)
- Related: `656b2a7e-create-config-support.md` (can be done in parallel)

## References
- [midori-ai-agent-base docs](https://github.com/Midori-AI-OSS/agents-packages/blob/main/midori-ai-agent-base/docs.md)
- [midori-ai-agent-openai docs](https://github.com/Midori-AI-OSS/agents-packages/blob/main/midori-ai-agent-openai/docs.md)
- [midori-ai-agent-huggingface docs](https://github.com/Midori-AI-OSS/agents-packages/blob/main/midori-ai-agent-huggingface/docs.md)
- [midori-ai-logger](https://github.com/Midori-AI-OSS/agents-packages/tree/main/logger)
- Current: `backend/llms/loader.py` (to be deleted)
- Current: `backend/llms/torch_checker.py` (keep)
- Current: `backend/llms/safety.py` (verify/update)

## Notes for Coder
- **BREAK backward compatibility** - this is intentional to find issues faster
- NO compatibility layer - all old code must be updated
- The framework's `get_agent()` handles backend selection automatically
- AgentPayload is more structured than the old text-only interface
- Remove ModelName enum completely - use strings directly
- Remove GGUF support - not needed with agent framework
- Use midori_ai_logger for all logging (replace `logging.getLogger()`)
- Primary: OpenAI agents (for API servers), Fallback: HuggingFace agents (local)
- The framework includes memory management - don't need custom implementation
- Streaming is built into the framework - simpler than custom implementation
- Verify safety.py functions work with agent framework model names
