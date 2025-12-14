# Agent Framework Migration Guide

## Overview

This guide helps developers migrate code from the legacy LLM loader to the Midori AI Agent Framework. The migration provides standardized interfaces, better features, and easier maintenance.

## Why Migrate?

### Benefits

1. **Standardized Interface**: Consistent API across all backends
2. **Better Configuration**: File-based config with environment variable fallback
3. **Built-in Features**: Memory management, tool support, streaming
4. **Easier Testing**: Framework includes test utilities and mocks
5. **Future-Proof**: New backends added via framework updates
6. **Less Code**: Remove custom wrappers and protocols

### Breaking Changes

The migration intentionally breaks backward compatibility in some areas to surface issues quickly. All old code must be updated to use the new interfaces.

## Migration Steps

### Step 1: Update Imports

#### Old

```python
from llms.loader import load_llm, ModelName, SupportsStream
from llms.loader import validate_lrm
```

#### New

```python
from llms.agent_loader import load_agent, validate_agent
from midori_ai_agent_base import AgentPayload, MidoriAiAgentProtocol
```

### Step 2: Replace Model Enums with Strings

The `ModelName` enum is removed. Use model name strings directly.

#### Old

```python
model = ModelName.OPENAI_20B.value  # "gpt-oss:20b"
llm = load_llm(model=model)
```

#### New

```python
model = "gpt-oss:20b"  # Direct string
agent = await load_agent(model=model)
```

### Step 3: Convert to Async/Structured Payloads

#### Old (Synchronous + String Prompts)

```python
llm = load_llm(model="gpt-oss:20b")
response = ""
async for chunk in llm.generate_stream(prompt):
    response += chunk
```

#### New (Asynchronous + Structured Payloads)

```python
agent = await load_agent(model="gpt-oss:20b")

payload = AgentPayload(
    user_message=prompt,
    thinking_blob="",
    system_context="You are a helpful assistant.",
    user_profile={},
    tools_available=[],
    session_id="chat-123",
)

response = await agent.invoke(payload)
# response.response contains the text
```

### Step 4: Update Validation

#### Old

```python
from llms.loader import validate_lrm

llm = load_llm(model="gpt-oss:20b")
is_valid = await validate_lrm(llm)
```

#### New

```python
from llms.agent_loader import validate_agent

agent = await load_agent(model="gpt-oss:20b")
is_valid = await validate_agent(agent)
```

### Step 5: Backend Selection

#### Old (Implicit)

```python
# Backend selected based on environment only
llm = load_llm(model="gpt-oss:20b")
```

#### New (Explicit Control)

```python
# Auto-detect (default)
agent = await load_agent(model="gpt-oss:20b")

# Force specific backend
agent = await load_agent(backend="openai", model="gpt-4")
agent = await load_agent(backend="huggingface", model="openai/gpt-oss-20b")
```

## Common Migration Patterns

### Pattern 1: Simple Text Generation

#### Old

```python
llm = load_llm()
response = ""
async for chunk in llm.generate_stream("What is 2+2?"):
    response += chunk
return response
```

#### New

```python
agent = await load_agent()
payload = AgentPayload(
    user_message="What is 2+2?",
    thinking_blob="",
    system_context="You are a math tutor.",
    user_profile={},
    tools_available=[],
    session_id="math-query",
)
response = await agent.invoke(payload)
return response.response
```

### Pattern 2: Chat with Context

#### Old

```python
llm = load_llm()
prompt = f"{previous_context}\nUser: {message}\nAssistant:"
response = ""
async for chunk in llm.generate_stream(prompt):
    response += chunk
```

#### New

```python
from midori_ai_agent_base import MemoryEntryData

agent = await load_agent()

# Build memory from conversation history
memory = []
for entry in conversation_history:
    memory.append(MemoryEntryData(
        role=entry['role'],
        content=entry['content']
    ))

payload = AgentPayload(
    user_message=message,
    memory=memory,  # Framework handles context
    system_context="You are a helpful assistant.",
    user_profile={},
    tools_available=[],
    session_id=f"chat-{user_id}",
)

response = await agent.invoke(payload)
```

### Pattern 3: Model Selection in Config

#### Old

```python
import os
model = os.getenv("AF_LLM_MODEL", "gpt-oss:20b")
llm = load_llm(model=model)
```

#### New

```python
# Option 1: Use config file (config.toml)
agent = await load_agent()  # Reads from config.toml

# Option 2: Environment variable (fallback)
agent = await load_agent()  # Reads AF_LLM_MODEL if no config

# Option 3: Explicit override
agent = await load_agent(model="gpt-4")  # Override config/env
```

## Configuration Migration

### From Environment Variables to Config File

#### Old (Environment Only)

```bash
export OPENAI_API_URL="http://localhost:11434/v1"
export OPENAI_API_KEY="not-needed"
export AF_LLM_MODEL="llama3:8b"
```

#### New (Config File)

Create `backend/config.toml`:

```toml
[midori_ai_agent_base]
backend = "openai"
model = "llama3:8b"
api_key = "${OPENAI_API_KEY}"  # Still uses env var
base_url = "${OPENAI_API_URL}"  # Still uses env var
```

Environment variables still work:

```bash
export OPENAI_API_URL="http://localhost:11434/v1"
export OPENAI_API_KEY="not-needed"
```

## Error Handling Migration

### Old

```python
try:
    llm = load_llm(model="gpt-oss:20b")
except Exception as e:
    # Generic exception handling
    logger.error(f"Failed to load LLM: {e}")
    raise
```

### New

```python
try:
    agent = await load_agent(model="gpt-oss:20b")
except ImportError:
    # Agent framework not installed
    logger.error("Agent framework not available. Install with: uv sync --extra llm-cpu")
    raise
except ValueError as e:
    # No backend available (configuration issue)
    logger.error(f"No backend available: {e}")
    logger.info("Set OPENAI_API_URL or install torch for local inference")
    raise
except Exception as e:
    # Other errors
    logger.error(f"Failed to load agent: {e}")
    raise
```

## Testing Migration

### Old Tests

```python
def test_llm_loading():
    llm = load_llm(model="gpt-oss:20b")
    assert llm is not None
```

### New Tests

```python
@pytest.mark.asyncio
async def test_agent_loading(monkeypatch):
    # Mock the framework if needed
    monkeypatch.setattr("llms.agent_loader._AGENT_FRAMEWORK_AVAILABLE", True)
    
    agent = await load_agent(model="gpt-oss:20b", validate=False)
    assert agent is not None
```

## Common Issues and Solutions

### Issue 1: ImportError - Agent Framework Not Available

**Error**: `ImportError: Agent framework is not available`

**Solution**: Install llm-cpu extras:

```bash
cd backend
uv sync --extra llm-cpu
```

### Issue 2: ValueError - No Backend Available

**Error**: `ValueError: No backend available`

**Solution**: Either:
- Set `OPENAI_API_URL` for OpenAI backend
- Install torch for HuggingFace backend: `uv sync --extra llm-cpu`
- Explicitly specify backend in config.toml

### Issue 3: ModelName No Longer Exists

**Error**: `AttributeError: module 'llms.loader' has no attribute 'ModelName'`

**Solution**: Replace enum with string:

```python
# Old
from llms.loader import ModelName
model = ModelName.OPENAI_20B.value

# New
model = "gpt-oss:20b"
```

### Issue 4: SupportsStream Protocol Missing

**Error**: `AttributeError: module 'llms.loader' has no attribute 'SupportsStream'`

**Solution**: Use `MidoriAiAgentProtocol`:

```python
# Old
from llms.loader import SupportsStream
def process_llm(llm: SupportsStream): ...

# New
from midori_ai_agent_base import MidoriAiAgentProtocol
async def process_agent(agent: MidoriAiAgentProtocol): ...
```

## Gradual Migration Strategy

For large codebases, migrate gradually:

1. **Phase 1**: Update core agent loading (config routes, main entry points)
2. **Phase 2**: Migrate high-traffic features (chat room, battle dialogue)
3. **Phase 3**: Update remaining features
4. **Phase 4**: Remove legacy loader completely

During migration, both loaders can coexist:

```python
# Try new framework first
try:
    from llms.agent_loader import load_agent
    agent = await load_agent()
    # Use agent...
except ImportError:
    # Fall back to legacy
    from llms.loader import load_llm
    llm = load_llm()
    # Use llm...
```

## Checklist

Use this checklist when migrating a module:

- [ ] Import statements updated
- [ ] `ModelName` enum replaced with strings
- [ ] Synchronous `load_llm()` replaced with async `load_agent()`
- [ ] String prompts converted to `AgentPayload` structures
- [ ] Streaming code updated (if applicable)
- [ ] Validation functions updated
- [ ] Error handling improved
- [ ] Tests updated to async
- [ ] Configuration migrated to config.toml (optional)
- [ ] Documentation updated
- [ ] Linting passes (`uv tool run ruff check`)

## Support and Resources

- [Agent Framework Documentation](.codex/implementation/agent-framework.md)
- [Config System Documentation](.codex/implementation/agent-config.md)
- [Midori AI agents-packages GitHub](https://github.com/Midori-AI-OSS/agents-packages)
- Test examples: `backend/tests/test_agent_loader.py`

## Questions?

If you encounter issues during migration:

1. Check existing migrated code for patterns (e.g., `routes/config.py`)
2. Review test files for examples
3. Consult framework documentation
4. Check task files in `.codex/tasks/` for migration notes
