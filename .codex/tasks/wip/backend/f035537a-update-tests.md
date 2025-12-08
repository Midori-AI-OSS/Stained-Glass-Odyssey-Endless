# Update Tests for Agent Framework

## Task ID
`f035537a-update-tests`

## Priority
Low

## Status
WIP

## Description
Update and expand test coverage for the Agent Framework migration. Ensure all LLM-related tests work with the new agent system.

## Context
Existing tests may reference:
- Old `load_llm()` function
- Custom wrapper classes
- Old protocols and interfaces

Need to add tests for:
- New agent loader
- Config file loading
- AgentPayload/AgentResponse usage
- All three backends

## Objectives
1. Update existing LLM tests
2. Add tests for new agent loader
3. Add tests for config support
4. Test all three backends
5. Test memory integration
6. Ensure backward compatibility tests

## Implementation Steps

### Step 1: Update Existing Tests
```bash
cd backend
grep -rn "load_llm\|SupportsStream" tests/ --include="*.py"
```

Update any tests that use old interfaces.

### Step 2: Add Agent Loader Tests
Create `tests/test_agent_loader.py`:
```python
import pytest
from llms.agent_loader import load_agent, validate_agent
from midori_ai_agent_base import AgentPayload


@pytest.mark.asyncio
async def test_load_agent_huggingface():
    agent = await load_agent(backend="huggingface")
    assert agent is not None


@pytest.mark.asyncio  
async def test_validate_agent():
    agent = await load_agent(backend="huggingface")
    is_valid = await validate_agent(agent)
    assert isinstance(is_valid, bool)


@pytest.mark.asyncio
async def test_agent_invoke():
    agent = await load_agent(backend="huggingface")
    payload = AgentPayload(
        user_message="Hello",
        thinking_blob="",
        system_context="You are helpful.",
        user_profile={},
        tools_available=[],
        session_id="test",
    )
    response = await agent.invoke(payload)
    assert hasattr(response, 'response')
```

### Step 3: Add Config Tests
Create `tests/test_config.py`:
```python
from llms.agent_loader import find_config_file, get_agent_config


def test_find_config():
    path = find_config_file()
    assert path is None or path.exists()


def test_get_config():
    config = get_agent_config()
    if config:
        assert config.backend in ["openai", "huggingface", "langchain"]
```

### Step 4: Add Integration Tests
Test chat room, config routes with agent framework.

### Step 5: Run Full Test Suite
```bash
cd backend
uv run pytest tests/ -v
```

## Acceptance Criteria
- [ ] All existing tests updated for new interfaces
- [ ] New tests added for agent loader
- [ ] New tests added for config support
- [ ] Tests cover all three backends
- [ ] Integration tests updated
- [ ] All tests pass
- [ ] Test coverage maintained or improved

## Dependencies
- Requires: All other migration tasks completed
- Should be done incrementally with each task

## References
- Tests directory: `backend/tests/`
- Framework test examples in agents-packages repo
