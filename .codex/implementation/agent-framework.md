# Agent Framework Implementation

## Overview

AutoFighter uses the [Midori AI Agent Framework](https://github.com/Midori-AI-OSS/agents-packages) for standardized LRM/LLM management. This provides a consistent interface across multiple backends, config file support, and built-in features like memory management and streaming.

## Architecture

### Core Components

1. **Agent Loader** (`backend/llms/agent_loader.py`)
   - Provides `load_agent()` function for creating agents
   - Supports multiple backends (OpenAI, HuggingFace, Langchain)
   - Auto-detects appropriate backend based on environment
   - Falls back gracefully when framework not installed

2. **Configuration System** (`backend/config.toml`)
   - TOML-based configuration file
   - Environment variable substitution (`${VAR_NAME}` syntax)
   - Backend-specific overrides
   - See `config.toml.example` for full documentation

3. **API Routes** (`backend/routes/config.py`)
   - `/config/lrm` - Get/set LRM configuration
   - `/config/lrm/test` - Test LRM with validation
   - Supports both agent framework and legacy loader

### Supported Backends

#### 1. OpenAI Backend (Primary)
- Used for: OpenAI API, Ollama, LocalAI, and compatible services
- Requirements: `OPENAI_API_URL` environment variable or config
- Activates when: URL is configured or backend explicitly set to "openai"
- Models: gpt-4, gpt-oss:20b, llama3:8b, etc.

#### 2. HuggingFace Backend (Fallback)
- Used for: Local inference with HuggingFace models
- Requirements: torch and transformers installed (llm-cpu extra)
- Activates when: OpenAI URL not set and torch available
- Recommended model: `openai/gpt-oss-20b` (high reasoning capability)

#### 3. Langchain Backend (Optional)
- Used for: Langchain integrations
- Requirements: langchain packages
- Activates when: Explicitly specified in config or code

## Configuration

### Priority Order

Settings are resolved in this order (highest to lowest):
1. Function arguments in code (e.g., `load_agent(backend="openai")`)
2. Config file backend-specific section (`[midori_ai_agent_base.openai]`)
3. Config file base section (`[midori_ai_agent_base]`)
4. Environment variables (`OPENAI_API_URL`, `AF_LLM_MODEL`)
5. Built-in defaults

### Example Configuration

```toml
[midori_ai_agent_base]
backend = "openai"
model = "gpt-oss:20b"
api_key = "${OPENAI_API_KEY}"
base_url = "${OPENAI_API_URL}"

[midori_ai_agent_base.huggingface]
model = "openai/gpt-oss-20b"
device = "auto"
temperature = 0.7
```

### Environment Variables

- `OPENAI_API_URL` - Base URL for OpenAI-compatible API (e.g., `http://localhost:11434/v1`)
- `OPENAI_API_KEY` - API key (can be "not-needed" for Ollama)
- `AF_LLM_MODEL` - Default model name if not specified in config

## Usage Examples

### Basic Usage

```python
from llms.agent_loader import load_agent
from midori_ai_agent_base import AgentPayload

# Load agent (auto-detects backend and model)
agent = await load_agent()

# Create payload
payload = AgentPayload(
    user_message="Hello, world!",
    thinking_blob="",
    system_context="You are a helpful assistant.",
    user_profile={},
    tools_available=[],
    session_id="example",
)

# Get response
response = await agent.invoke(payload)
print(response.response)
```

### Backend-Specific Loading

```python
# Force OpenAI backend
agent = await load_agent(backend="openai", model="gpt-4")

# Force HuggingFace backend with specific model
agent = await load_agent(
    backend="huggingface",
    model="openai/gpt-oss-20b"
)
```

### Config File Loading

```python
from llms.agent_loader import get_agent_config

# Get current config
config = get_agent_config()
if config:
    print(f"Backend: {config.backend}")
    print(f"Model: {config.model}")
```

### Validation

```python
from llms.agent_loader import validate_agent

# Validate agent is working
agent = await load_agent()
is_valid = await validate_agent(agent)
if is_valid:
    print("Agent validation passed!")
```

## Memory Management

The agent framework includes built-in memory support via `AgentPayload.memory` field:

```python
from midori_ai_agent_base import MemoryEntryData

memory = [
    MemoryEntryData(role="user", content="What is 2+2?"),
    MemoryEntryData(role="assistant", content="4"),
]

payload = AgentPayload(
    user_message="What was my last question?",
    memory=memory,  # Include conversation history
    # ... other fields
)
```

For persistent memory, consider integrating `midori-ai-agent-context-manager` (not yet implemented in AutoFighter).

## Error Handling

The agent loader gracefully handles missing dependencies:

```python
try:
    agent = await load_agent()
except ImportError as e:
    # Agent framework not installed
    print(f"Agent framework not available: {e}")
    # Fall back to legacy loader or show installation instructions
except ValueError as e:
    # No backend available (no OpenAI URL and torch not installed)
    print(f"No backend available: {e}")
```

## Testing

### Unit Tests

See `backend/tests/test_agent_loader.py` for comprehensive test coverage:
- Backend selection logic
- Config file loading
- Environment variable fallback
- Validation functionality
- Error handling

### Manual Testing

```bash
# Test config loading
cd backend
uv run python test_config.py

# Validate config file
uv run python scripts/validate_config.py

# Test without config (env vars only)
mv config.toml config.toml.bak
uv run python test_config.py
mv config.toml.bak config.toml
```

## Migration from Legacy Loader

### Old Interface (Deprecated)

```python
from llms.loader import load_llm, ModelName

llm = load_llm(model=ModelName.OPENAI_20B.value)
response = ""
async for chunk in llm.generate_stream(prompt):
    response += chunk
```

### New Interface (Current)

```python
from llms.agent_loader import load_agent
from midori_ai_agent_base import AgentPayload

agent = await load_agent(model="gpt-oss:20b")
payload = AgentPayload(user_message=prompt, ...)
response = await agent.invoke(payload)
print(response.response)
```

### Key Differences

1. **Structured Payloads**: AgentPayload instead of raw text
2. **Consistent Interface**: Same protocol across all backends
3. **Built-in Features**: Memory, tools, streaming support included
4. **Config Support**: File-based configuration instead of code/env only
5. **Better Validation**: Standardized validation across backends

## Integration Points

### Chat Room (`autofighter/rooms/chat.py`)

Currently being redesigned to use per-character agents with memory and event-driven responses. See task `c0f04e25-update-chat-room.md` for details.

### Config Routes (`routes/config.py`)

The `/config/lrm` endpoints support both agent framework and legacy loader:
1. Try agent framework first (preferred)
2. Fall back to legacy loader if framework not available
3. Return backend type in response ("agent" or "legacy")

### WebUI Settings

Frontend settings menu (`frontend/src/lib/components/LLMSettings.svelte`) allows users to:
- Select backend (OpenAI/HuggingFace)
- Configure API URL (for OpenAI)
- Select model
- Test connection

## Future Enhancements

1. **Memory Persistence**: Integrate `midori-ai-agent-context-manager` for long-term memory
2. **Tool Support**: Add game-specific tools for agents to use
3. **Streaming**: Implement streaming responses in chat room
4. **Advanced Backends**: Support additional backends as framework adds them
5. **Per-Character Agents**: Dedicated agents for each character with personalities

## References

- [Midori AI Agent Framework](https://github.com/Midori-AI-OSS/agents-packages)
- [midori-ai-agent-base docs](https://github.com/Midori-AI-OSS/agents-packages/blob/main/midori-ai-agent-base/docs.md)
- [midori-ai-agent-openai docs](https://github.com/Midori-AI-OSS/agents-packages/blob/main/midori-ai-agent-openai/docs.md)
- [midori-ai-agent-huggingface docs](https://github.com/Midori-AI-OSS/agents-packages/blob/main/midori-ai-agent-huggingface/docs.md)
- [Config System Documentation](.codex/implementation/agent-config.md)

## Change Log

- **2025-12-14**: Created comprehensive agent framework documentation
- **2025-12-08**: Initial agent loader implementation
- **2025-12-07**: Agent framework dependencies added to pyproject.toml
