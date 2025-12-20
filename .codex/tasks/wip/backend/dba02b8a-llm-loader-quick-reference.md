# LLM Loader Migration - Quick Reference Summary

## Document ID
`dba02b8a-llm-loader-quick-reference`

## Overview
Quick reference for the LLM loader migration from custom `loader.py` to Midori AI Agent Framework.

**Parent Task**: [32e92203-migrate-llm-loader.md](./32e92203-migrate-llm-loader.md)  
**Full Plan**: [2792ed45-llm-loader-migration-execution-plan.md](./2792ed45-llm-loader-migration-execution-plan.md)

---

## Current Status (at start)

### ✅ Already Complete
- `backend/llms/agent_loader.py` - Fully implemented
- `load_agent()` function with config support
- `validate_agent()` function
- Config file discovery and loading

### 🔧 Needs Migration (14 call sites)
**Production files (6):**
1. `autofighter/rooms/chat.py` - Chat room
2. `routes/config.py` - Config endpoints
3. `app.py` - App startup
4. `plugins/characters/foe_base.py` - Foe AI
5. `plugins/characters/_base.py` - Character AI
6. `scripts/validate_config.py` - Already uses new interface ✓

**Test files (8):**
1. `tests/test_llm_loader.py` - Main loader tests
2. `tests/test_chat_room.py` - Chat mocks
3. `tests/test_config_lrm.py` - Config mocks
4. `tests/test_accelerate_dependency.py` - Dependency tests
5. `tests/test_accelerate_fix_verification.py` - More dependency tests
6. `tests/test_event_bus.py` - Event bus mocks
7. `tests/test_effects.py` - Effects mocks
8. `tests/conftest.py` - Global fixtures

---

## Quick Migration Guide

### Step 1: Update Imports
```python
# OLD
from llms.loader import ModelName, load_llm

# NEW
from llms import load_agent
from midori_ai_agent_base import AgentPayload  # if using structured prompts
```

### Step 2: Update Loading
```python
# OLD
llm = await asyncio.to_thread(load_llm, model)

# NEW
agent = await load_agent(model=model)  # Already async
```

### Step 3: Update Usage
```python
# OLD
async for chunk in llm.generate_stream(prompt_text):
    yield chunk

# NEW
payload = AgentPayload(
    user_message=prompt_text,
    system_context="You are helpful.",
    thinking_blob="",
    user_profile={},
    tools_available=[],
    session_id="session_id"
)
async for chunk in agent.stream(payload):
    yield chunk
```

### Step 4: Update Tests/Mocks
```python
# OLD
monkeypatch.setattr("llms.loader.load_llm", fake_loader)

# NEW
monkeypatch.setattr("llms.load_agent", fake_loader)
```

---

## 8 Phases at a Glance

| # | Phase | Time | Key Actions |
|---|-------|------|-------------|
| 1 | Pre-Flight | 30m | Verify deps, create backups |
| 2 | Core Module | 1-2h | Update __init__.py, delete loader.py |
| 3 | Simple Sites | 1-2h | app.py, config.py |
| 4 | Plugins | 2-3h | Character AI files |
| 5 | Chat Room | 1h | Minimal update (full redesign later) |
| 6 | Tests | 2-3h | All 8 test files |
| 7 | Safety.py | 30m | Remove GGUF, verify functions |
| 8 | Validation | 1h | Full test suite, linting, builds |

**Total: 9-13 hours**

---

## Breaking Changes Checklist

- [ ] `load_llm()` function - **REMOVED**
- [ ] `ModelName` enum - **REMOVED**
- [ ] `SupportsStream` protocol - **REMOVED**
- [ ] `validate_lrm()` function - **REMOVED**
- [ ] GGUF support - **REMOVED**
- [ ] `gguf_strategy()` in safety.py - **REMOVED**

### New Interfaces Only
- ✅ `load_agent()` - Use this
- ✅ `validate_agent()` - Use this
- ✅ `get_agent_config()` - Use this
- ✅ `MidoriAiAgentProtocol` - Use this
- ✅ `AgentPayload` / `AgentResponse` - Use this

---

## Critical File Changes

### `backend/llms/__init__.py` (Phase 2)
```python
"""LLM and agent loading utilities - NEW AGENT FRAMEWORK ONLY."""

# New agent framework interface (ONLY interface now)
from .agent_loader import load_agent
from .agent_loader import validate_agent
from .agent_loader import get_agent_config

# Keep existing utilities
from .torch_checker import is_torch_available
from .torch_checker import require_torch

__all__ = [
    # New interface (breaking change - old code must update)
    "load_agent",
    "validate_agent",
    "get_agent_config",
    # Utilities
    "is_torch_available",
    "require_torch",
]

# OLD INTERFACES REMOVED:
# - load_llm() - REMOVED, use load_agent() instead
# - SupportsStream - REMOVED, use MidoriAiAgentProtocol instead
# - ModelName - REMOVED, use string literals instead
```

### Delete `backend/llms/loader.py` (Phase 2)
```bash
rm backend/llms/loader.py
# Or for safety: mv backend/llms/loader.py backend/llms/loader.py.old.bak
```

---

## Task Dependencies

### Must Complete First
- [ ] **12af34e9-update-dependencies.md** - Install agent framework packages

### Blocks These Tasks
- [ ] **c0f04e25-update-chat-room.md** - Chat room redesign
- [ ] **f035537a-update-tests.md** - Comprehensive tests
- [ ] **4bf8abe6-update-documentation.md** - Docs

### Already Complete
- ✅ **96e5fdb9-update-config-routes.md** - Config routes

### Can Run Parallel
- [ ] **656b2a7e-create-config-support.md** - Config file template

---

## Validation Commands

### Check Dependencies
```bash
cd backend
uv run python -c "from midori_ai_agent_base import get_agent; print('✓ OK')"
uv run python -c "from midori_ai_logger import get_logger; print('✓ OK')"
```

### Test Agent Loading
```bash
cd backend
uv run python -c "import asyncio; from llms import load_agent; asyncio.run(load_agent())"
```

### Run Tests
```bash
cd backend
uv run pytest tests/test_llm_loader.py -v  # Will fail until updated
```

### Run Linting
```bash
cd backend
uv tool run ruff check . --fix
```

### Test Backend
```bash
cd backend
uv run python app.py &
curl http://localhost:59002/
pkill -f "python app.py"
```

---

## Risk Mitigation

### High Risks
1. **Character AI Behavior** - Test thoroughly, have rollback ready
2. **Breaking Changes** - Clear docs, version bump
3. **Test Coverage** - Run full suite multiple times

### Rollback if Needed
```bash
cd backend/llms
git checkout HEAD~1 loader.py __init__.py
# Revert other changes as needed
```

---

## Success Criteria

**Must Have:**
- [ ] Old loader.py deleted
- [ ] All `load_llm()` calls replaced with `load_agent()`
- [ ] All `ModelName` references removed
- [ ] Linting passes
- [ ] App starts successfully

**Should Have:**
- [ ] Test suite passes (or failures documented)
- [ ] Character AI functional
- [ ] Chat room functional

---

## Coder Assignment Strategy

### Delegate to Coder (Low Risk)
- Update simple call sites (app.py, config.py)
- Update test mocks
- Update __init__.py exports
- Delete loader.py

### Needs Review (Medium Risk)
- Character plugin updates
- Test file rewrites
- Safety.py cleanup

### Task Master Oversight (High Risk)
- Final integration testing
- Breaking change validation
- Documentation of issues

---

## Related Documents

- **Full Execution Plan**: [2792ed45-llm-loader-migration-execution-plan.md](./2792ed45-llm-loader-migration-execution-plan.md)
- **Parent Task**: [32e92203-migrate-llm-loader.md](./32e92203-migrate-llm-loader.md)
- **Goal Document**: [GOAL-midori-ai-agent-framework-migration.md](./GOAL-midori-ai-agent-framework-migration.md)
- **Chat Room Redesign**: [c0f04e25-update-chat-room.md](./c0f04e25-update-chat-room.md)
- **Config Support**: [656b2a7e-create-config-support.md](../656b2a7e-create-config-support.md)

---

## Last Updated
2025-12-20 by Task Master

**Status**: Ready for implementation
**Estimated Effort**: 9-13 hours
**Complexity**: High (breaking changes)
**Priority**: High (blocks other tasks)
