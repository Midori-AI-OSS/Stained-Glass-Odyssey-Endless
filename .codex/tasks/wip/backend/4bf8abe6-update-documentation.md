# Update Documentation for Agent Framework

## Task ID
`4bf8abe6-update-documentation`

## Priority
Low

## Status
WIP

## Description
Update all documentation to reflect the migration to the Midori AI Agent Framework. This includes implementation docs, README files, and developer guides.

## Context
Documentation needs updates in:
- `backend/README.md` - Backend setup and usage
- `.codex/implementation/` - Technical implementation docs
- `BUILD.md` - Build process documentation
- `DEVELOPMENT.md` - Development guide
- Docstrings in migrated code

## Objectives
1. Update backend README with new agent setup
2. Create implementation doc for agent framework
3. Update build documentation
4. Update development guide
5. Add migration guide
6. Update API documentation
7. Add examples

## Implementation Steps

### Step 1: Update Backend README
Add sections to `backend/README.md`:
```markdown
## Agent Framework

AutoFighter uses the [Midori AI Agent Framework](https://github.com/Midori-AI-OSS/agents-packages) for LRM/LLM management.

### Configuration

See [Configuration](#configuration) section for setup.

### Supported Backends

1. **OpenAI** - OpenAI API, Ollama, and compatible services
2. **HuggingFace** - Local inference with HuggingFace models
3. **Langchain** - Langchain backend

### Usage Examples

```python
from llms.agent_loader import load_agent
from midori_ai_agent_base import AgentPayload

# Load agent
agent = await load_agent()

# Create payload
payload = AgentPayload(
    user_message="Hello!",
    thinking_blob="",
    system_context="You are helpful.",
    user_profile={},
    tools_available=[],
    session_id="example",
)

# Get response
response = await agent.invoke(payload)
print(response.response)
```
```

### Step 2: Create Agent Implementation Doc
Create `.codex/implementation/agent-framework.md`:
```markdown
# Agent Framework Implementation

## Overview
AutoFighter uses the Midori AI Agent Framework for standardized LRM/LLM management.

## Architecture
- Agent Loader: `backend/llms/agent_loader.py`
- Config Support: `backend/config.toml`
- Backends: OpenAI, HuggingFace, Langchain

## Components
### Agent Loader
Provides `load_agent()` function...

### Configuration
Supports config.toml and env vars...

### Memory Management
Uses AgentPayload.memory field...

## Migration Notes
Migrated from custom llms/loader.py to agent framework on [DATE].

## References
- [Agent Framework](https://github.com/Midori-AI-OSS/agents-packages)
- [Config Guide](.codex/implementation/agent-config.md)
```

### Step 3: Update Build Documentation
Update `BUILD.md`:
```markdown
## LLM Dependencies

The `llm-cpu` extra includes:
- midori-ai-agents-all - Agent framework meta-package
- torch, transformers - Local model support
- Other LLM dependencies
```

### Step 4: Update Development Guide
Update `DEVELOPMENT.md`:
```markdown
## Agent Configuration

Configure agents via config.toml or environment variables.
See backend/config.toml.example for details.
```

### Step 5: Create Migration Guide
Create `.codex/implementation/agent-migration-guide.md`:
```markdown
# Agent Framework Migration Guide

## Overview
Guide for developers migrating code to use the agent framework.

## Old vs New

### Loading Models
**Old:**
```python
from llms.loader import load_llm
llm = load_llm(model="openai/gpt-oss-20b")
async for chunk in llm.generate_stream(prompt):
    print(chunk)
```

**New:**
```python
from llms.agent_loader import load_agent
from midori_ai_agent_base import AgentPayload

agent = await load_agent()
payload = AgentPayload(user_message=prompt, ...)
response = await agent.invoke(payload)
print(response.response)
```

## Breaking Changes
- None for end users (backward compat maintained)
- API changes for developers using llms module

## Benefits
- Standardized interface
- Better features
- Easier maintenance
```

### Step 6: Update Docstrings
Ensure all new code has proper docstrings:
- `agent_loader.py`
- `compat.py`
- Updated files

### Step 7: Add CHANGELOG Entry
Update `CHANGELOG.md` (if exists) or create migration notes.

## Acceptance Criteria
- [ ] backend/README.md updated
- [ ] .codex/implementation/agent-framework.md created
- [ ] .codex/implementation/agent-migration-guide.md created
- [ ] BUILD.md updated
- [ ] DEVELOPMENT.md updated
- [ ] All new code has docstrings
- [ ] Examples added
- [ ] Migration notes documented

## Dependencies
- Requires: All other migration tasks completed
- Should be done as tasks are completed

## References
- Backend: `backend/README.md`
- Implementation: `.codex/implementation/`
- Build: `BUILD.md`
- Development: `DEVELOPMENT.md`
