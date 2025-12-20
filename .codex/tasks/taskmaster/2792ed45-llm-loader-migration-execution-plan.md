# LLM Loader Migration - Comprehensive Execution Plan

## Document ID
`2792ed45-llm-loader-migration-execution-plan`

## Parent Task
[32e92203-migrate-llm-loader.md](./32e92203-migrate-llm-loader.md)

## Purpose
This document provides a comprehensive, actionable execution plan for migrating from the custom `loader.py` to the Midori AI Agent Framework. It breaks down the work into clear phases with specific tasks, identifies dependencies, and provides guidance for coders.

## Status Assessment

### ✅ COMPLETED
- `backend/llms/agent_loader.py` - Fully implemented with:
  - `load_agent()` function with config file support
  - `validate_agent()` function  
  - `get_agent_config()` helper
  - `find_config_file()` helper
  - Environment variable fallback
  - Backend auto-detection (OpenAI → HuggingFace)
  - Proper logging with midori_ai_logger
  - Log sanitization for security

### 🔄 IN PROGRESS
- Task 32e92203-migrate-llm-loader.md (this migration)

### ⏳ BLOCKED/WAITING
- Task 12af34e9-update-dependencies.md (prerequisite - must verify completion)

### 📋 TODO (This Plan)
- Update `llms/__init__.py` to export only new interfaces
- Delete old `loader.py` (BREAKING CHANGE)
- Update all call sites to use new interfaces
- Remove `ModelName` enum references
- Update all test files
- Verify `safety.py` compatibility

---

## Dependencies and Related Tasks

### Prerequisites (MUST be complete first)
- [ ] **12af34e9-update-dependencies.md** - Verify agent framework packages installed
  - `midori-ai-agent-base`
  - `midori-ai-agent-openai`
  - `midori-ai-agent-huggingface`
  - `midori-ai-logger`

### Can Run in Parallel
- [ ] **656b2a7e-create-config-support.md** - Config file template and docs
- [ ] **5900934d-update-memory-management.md** - Memory features (separate concern)

### Blocked Until This Completes
- [ ] **c0f04e25-update-chat-room.md** - Chat room redesign (depends on agent interface)
- [ ] **f035537a-update-tests.md** - Comprehensive test suite updates
- [ ] **4bf8abe6-update-documentation.md** - Documentation updates

### Already Complete
- ✅ **96e5fdb9-update-config-routes.md** - Config routes updated (marked COMPLETED)

---

## Call Site Inventory

### Current `load_llm()` Call Sites (14 total)

#### Production Code (6 files)
1. **`backend/autofighter/rooms/chat.py`** (lines 7-8, 33)
   - Imports: `ModelName`, `load_llm`
   - Usage: `llm = await asyncio.to_thread(load_llm, model)`
   - Complexity: **MEDIUM** - Chat room being redesigned
   - Action: Minimal update for now, full redesign in c0f04e25

2. **`backend/routes/config.py`** (lines 5, 147-150, 190)
   - Imports: `ModelName`, `load_llm`, `load_agent`, `validate_agent`, `validate_lrm`
   - Usage: Mixed old and new interfaces
   - Complexity: **LOW** - Already partially migrated
   - Action: Remove old imports, update remaining uses

3. **`backend/app.py`** (lines 207, 224)
   - Imports: `load_llm`
   - Usage: `llm = await asyncio.to_thread(load_llm, model, validate=False)`
   - Complexity: **LOW** - Simple startup validation
   - Action: Replace with `load_agent(model=model, validate=False)`

4. **`backend/plugins/characters/foe_base.py`** (lines 131, 198, 207-208)
   - Imports: Conditional `is_torch_available`, `load_llm`
   - Usage: `llm = await asyncio.to_thread(load_llm)`
   - Complexity: **MEDIUM** - Character AI logic
   - Action: Update to use `load_agent()`, verify character AI still works

5. **`backend/plugins/characters/_base.py`** (lines 350, 433, 442-443)
   - Imports: Conditional `is_torch_available`, `load_llm`
   - Usage: `llm = await asyncio.to_thread(load_llm)`
   - Complexity: **MEDIUM** - Base character AI logic
   - Action: Update to use `load_agent()`, verify character AI still works

6. **`backend/scripts/validate_config.py`** (line 8)
   - Imports: `load_agent_config` from agent_loader
   - Complexity: **NONE** - Already using new interface
   - Action: None needed

#### Test Files (8 files)
7. **`backend/tests/test_llm_loader.py`** (lines 3, 63, 83, 98, 135, 148, 168)
   - Heavy usage of `ModelName` enum and `load_llm()`
   - Complexity: **HIGH** - Needs complete rewrite
   - Action: Rewrite to test `load_agent()` instead

8. **`backend/tests/test_chat_room.py`** (line 41)
   - Mocks: `monkeypatch.setattr("autofighter.rooms.chat.load_llm", fake_loader)`
   - Complexity: **LOW** - Just update mock path
   - Action: Update to mock `load_agent` instead

9. **`backend/tests/test_config_lrm.py`** (line 109)
   - Mocks: `monkeypatch.setattr("llms.loader.load_llm", fake_loader)`
   - Complexity: **LOW** - Just update mock path
   - Action: Update to mock `load_agent` instead

10. **`backend/tests/test_accelerate_dependency.py`** (lines 8, 30, 34, 60, 63)
    - Tests `ModelName.DEEPSEEK` with `load_llm()`
    - Complexity: **MEDIUM** - Tests dependency loading
    - Action: Update to use model strings and `load_agent()`

11. **`backend/tests/test_accelerate_fix_verification.py`** (lines 36, 39)
    - Tests `ModelName.DEEPSEEK` with `load_llm()`
    - Complexity: **LOW** - Similar to above
    - Action: Update to use model strings and `load_agent()`

12. **`backend/tests/test_event_bus.py`** (line 65)
    - Mocks: `loader_module.load_llm = lambda *args, **kwargs: None`
    - Complexity: **LOW** - Just update mock
    - Action: Update to mock `load_agent` instead

13. **`backend/tests/test_effects.py`** (line 42)
    - Mocks: `llms_loader.load_llm = lambda *_, **__: None`
    - Complexity: **LOW** - Just update mock
    - Action: Update to mock `load_agent` instead

14. **`backend/tests/conftest.py`** (line 230)
    - Mocks: `loader.load_llm = lambda *args, **kwargs: None`
    - Complexity: **LOW** - Just update mock
    - Action: Update to mock `load_agent` instead

### Current `ModelName` Enum References (8 files)
- `backend/autofighter/rooms/chat.py` - Line 7
- `backend/routes/config.py` - Line 5
- `backend/tests/test_accelerate_dependency.py` - Line 8
- `backend/tests/test_llm_loader.py` - Multiple uses
- `backend/tests/test_accelerate_fix_verification.py` - Line usage
- `backend/llms/loader.py` - Definition (will be deleted)

**Action**: Remove all `ModelName` imports and replace with string literals

---

## Execution Plan - Detailed Phases

### PHASE 1: Pre-Flight Verification (15-30 minutes)
**Goal**: Ensure all prerequisites are met before starting breaking changes

#### Tasks:
- [ ] **1.1** Verify dependency installation
  ```bash
  cd backend
  uv run python -c "from midori_ai_agent_base import get_agent; print('✓ Agent framework available')"
  uv run python -c "from midori_ai_logger import get_logger; print('✓ Logger available')"
  ```

- [ ] **1.2** Review agent_loader.py completeness
  ```bash
  cd backend/llms
  # Verify all functions exist
  grep -n "^async def load_agent" agent_loader.py
  grep -n "^async def validate_agent" agent_loader.py
  grep -n "^def get_agent_config" agent_loader.py
  grep -n "^def find_config_file" agent_loader.py
  ```

- [ ] **1.3** Create backup of current state
  ```bash
  cd backend/llms
  cp loader.py loader.py.backup-$(date +%Y%m%d)
  cp __init__.py __init__.py.backup-$(date +%Y%m%d)
  ```

- [ ] **1.4** Run baseline tests (expect some failures)
  ```bash
  cd backend
  uv run pytest tests/test_llm_loader.py -v
  ```

**Checkpoint**: All dependencies installed, backups created, baseline understood

---

### PHASE 2: Core Module Migration (1-2 hours)
**Goal**: Make the breaking change to the llms module itself

#### Tasks:
- [ ] **2.1** Update `backend/llms/__init__.py` (BREAKING CHANGE)
  - Remove exports: `load_llm`, `ModelName`, `SupportsStream`, `validate_lrm`
  - Export only: `load_agent`, `validate_agent`, `get_agent_config`
  - Keep utilities: `is_torch_available`, `require_torch`
  - See implementation in task 32e92203 Step 3

- [ ] **2.2** Delete old loader
  ```bash
  cd backend/llms
  rm loader.py  # Or mv to loader.py.old.bak
  ```

- [ ] **2.3** Verify imports still work
  ```bash
  cd backend
  uv run python -c "from llms import load_agent, validate_agent; print('✓ New exports work')"
  uv run python -c "from llms import load_llm" 2>&1 | grep "ImportError" && echo "✓ Old exports removed"
  ```

- [ ] **2.4** Run linting
  ```bash
  cd backend
  uv tool run ruff check llms --fix
  ```

**Checkpoint**: Old loader deleted, new interface exported, linting passes

---

### PHASE 3: Simple Call Site Updates (1-2 hours)
**Goal**: Update production files with straightforward migrations

#### Tasks:
- [ ] **3.1** Update `backend/app.py`
  - Change import: `from llms import load_agent` (remove load_llm)
  - Change usage: `agent = await load_agent(model=model, validate=False)`
  - Remove `asyncio.to_thread()` wrapper (load_agent is already async)
  - Update variable names: `llm` → `agent`

- [ ] **3.2** Update `backend/routes/config.py`
  - Remove import: `ModelName`, `load_llm`, `validate_lrm`
  - Keep imports: `load_agent`, `validate_agent` (already present)
  - Update `/config/lrm/test` endpoint to use `load_agent()` and `validate_agent()`
  - Remove any ModelName enum references
  - Update to use `AgentPayload` for structured prompts

- [ ] **3.3** Test simple updates
  ```bash
  cd backend
  uv run python app.py &
  # Wait for startup
  curl http://localhost:59002/
  # Should see {"flavor":"default","status":"ok"}
  pkill -f "python app.py"
  ```

**Checkpoint**: App starts successfully, basic endpoints work

---

### PHASE 4: Character Plugin Updates (2-3 hours)
**Goal**: Update character AI to use new agent interface

#### Tasks:
- [ ] **4.1** Update `backend/plugins/characters/_base.py`
  - Line 442-443: Change `from llms.loader import load_llm` → `from llms import load_agent`
  - Change: `llm = await asyncio.to_thread(load_llm)` → `agent = await load_agent()`
  - Update streaming logic to use `MidoriAiAgentProtocol.stream()` instead of `generate_stream()`
  - Update payload format from raw strings to `AgentPayload`

- [ ] **4.2** Update `backend/plugins/characters/foe_base.py`
  - Line 207-208: Same changes as _base.py
  - Verify conditional imports still work
  - Ensure torch_checker integration remains functional

- [ ] **4.3** Test character AI (if possible)
  ```bash
  cd backend
  # Run relevant character tests
  uv run pytest tests/ -k "character" -v
  ```

**Checkpoint**: Character plugins updated, conditional imports work

---

### PHASE 5: Chat Room Minimal Update (1 hour)
**Goal**: Get chat room working with new interface (full redesign deferred)

**Note**: Full chat room redesign is in task c0f04e25. This is minimal migration only.

#### Tasks:
- [ ] **5.1** Update `backend/autofighter/rooms/chat.py`
  - Remove imports: `ModelName`, `load_llm`
  - Add imports: `load_agent`, `AgentPayload` from midori_ai_agent_base
  - Change: `llm = await asyncio.to_thread(load_llm, model)` → `agent = await load_agent(model=model)`
  - Update streaming to use agent.stream() with AgentPayload
  - Keep minimal changes - full redesign is separate task

- [ ] **5.2** Test chat room (manual)
  ```bash
  cd backend
  uv run python app.py
  # Test chat room endpoints
  ```

**Checkpoint**: Chat room functional with new interface

---

### PHASE 6: Test File Updates (2-3 hours)
**Goal**: Update all test files to use new interface

#### Tasks:
- [ ] **6.1** Rewrite `backend/tests/test_llm_loader.py`
  - Rename to `test_agent_loader.py` (if preferred)
  - Replace all `ModelName` references with string literals
  - Replace `load_llm()` calls with `load_agent()`
  - Update validation tests to use `validate_agent()`
  - Remove GGUF tests (support dropped)
  - Test both OpenAI and HuggingFace backends

- [ ] **6.2** Update mock-based tests
  - `test_chat_room.py`: Update mock to `load_agent`
  - `test_config_lrm.py`: Update mock to `load_agent`
  - `test_event_bus.py`: Update mock to `load_agent`
  - `test_effects.py`: Update mock to `load_agent`
  - `conftest.py`: Update fixture mocks to `load_agent`

- [ ] **6.3** Update accelerate tests
  - `test_accelerate_dependency.py`: Remove `ModelName`, use strings
  - `test_accelerate_fix_verification.py`: Remove `ModelName`, use strings
  - Update to call `load_agent()` instead of `load_llm()`

- [ ] **6.4** Run full test suite
  ```bash
  cd backend
  uv run pytest tests/ -v --tb=short
  ```

**Checkpoint**: All tests updated and passing

---

### PHASE 7: Safety.py Verification (30 minutes)
**Goal**: Ensure safety.py functions work with new agent framework

#### Tasks:
- [ ] **7.1** Review `backend/llms/safety.py`
  ```bash
  cd backend/llms
  cat safety.py
  ```

- [ ] **7.2** Identify functions to keep/remove:
  - `model_memory_requirements()` - **KEEP** (works with HuggingFace model names)
  - `pick_device()` - **KEEP** (device selection still needed)
  - `gguf_strategy()` - **REMOVE** (GGUF support dropped)

- [ ] **7.3** Remove GGUF support
  ```bash
  cd backend/llms
  # Remove gguf_strategy() function
  # Update any imports/exports that reference it
  ```

- [ ] **7.4** Test safety functions
  ```bash
  cd backend
  uv run python -c "from llms.safety import model_memory_requirements; print(model_memory_requirements('openai/gpt-oss-20b'))"
  uv run python -c "from llms.safety import pick_device; print(pick_device())"
  ```

**Checkpoint**: Safety.py cleaned up and functional

---

### PHASE 8: Final Validation (1 hour)
**Goal**: Comprehensive validation of the migration

#### Tasks:
- [ ] **8.1** Run complete test suite
  ```bash
  cd /home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter
  ./run-tests.sh
  # Allow 2+ minutes for completion
  ```

- [ ] **8.2** Run linting on entire backend
  ```bash
  cd backend
  uv tool run ruff check . --fix
  ```

- [ ] **8.3** Manual smoke tests
  - Start backend: `cd backend && uv run python app.py`
  - Test basic endpoint: `curl http://localhost:59002/`
  - Test config endpoint: `curl http://localhost:59002/config/lrm`
  - Test LRM validation: `curl -X POST http://localhost:59002/config/lrm/test -d '{"prompt": "Hello"}'`

- [ ] **8.4** Verify builds still work
  ```bash
  ./build.sh non-llm
  ls -lh backend/dist/
  ```

- [ ] **8.5** Document any known issues
  - List any test failures (if any)
  - Note any functionality changes
  - Document any breaking changes for users

**Checkpoint**: All tests pass, linting clean, builds work

---

## Risk Assessment and Mitigation

### High Risk Areas

#### 1. Character AI Behavior Changes
**Risk**: Character AI responses might differ due to different agent interfaces  
**Mitigation**: 
- Extensive testing of character plugins
- Compare responses before/after if possible
- Have rollback plan ready

#### 2. Breaking Changes Impact
**Risk**: Users with custom code might break  
**Mitigation**: 
- Clear documentation of breaking changes
- Migration guide for custom code
- Version bump to signal breaking change

#### 3. Test Coverage Gaps
**Risk**: Some edge cases might not be tested  
**Mitigation**: 
- Run full test suite multiple times
- Manual testing of critical paths
- Monitor for issues in first few releases

### Medium Risk Areas

#### 4. Configuration Complexity
**Risk**: New config system might confuse users  
**Mitigation**: 
- Provide clear config examples
- Good defaults that work out of box
- Config validation with helpful errors

#### 5. Performance Changes
**Risk**: New agent framework might have different performance  
**Mitigation**: 
- Benchmark before/after if possible
- Monitor response times
- Optimize if regressions found

---

## Acceptance Criteria

### Must Have (Blocking)
- [ ] Old `loader.py` deleted
- [ ] `llms/__init__.py` exports only new interfaces
- [ ] All production code updated to use `load_agent()`
- [ ] All test files updated and passing
- [ ] `ModelName` enum completely removed
- [ ] Linting passes (`uv tool run ruff check backend --fix`)
- [ ] App starts and basic endpoints work
- [ ] No `load_llm()` or `ModelName` references in codebase (except backups)

### Should Have (Important)
- [ ] All tests pass (or failures documented)
- [ ] Character AI still functional
- [ ] Chat room still functional
- [ ] Config endpoints updated
- [ ] GGUF support removed from safety.py
- [ ] Build succeeds for non-llm variant

### Nice to Have (Optional)
- [ ] Performance benchmarks show no regression
- [ ] Migration guide written
- [ ] Config examples provided
- [ ] Build succeeds for llm variants

---

## Rollback Plan

If critical issues are discovered:

1. **Immediate Rollback**:
   ```bash
   cd backend/llms
   git checkout HEAD~1 loader.py __init__.py
   # Revert any call site changes
   git checkout HEAD~1 autofighter/ routes/ plugins/
   ```

2. **Selective Rollback**:
   - Restore backup files: `cp loader.py.backup-YYYYMMDD loader.py`
   - Restore old exports in `__init__.py`
   - Keep new `agent_loader.py` for future use

3. **Document Issues**:
   - File bug reports for any issues found
   - Update this plan with lessons learned
   - Plan fixes before attempting migration again

---

## Success Metrics

After completion, verify:
- ✅ Zero references to `load_llm()` in production code
- ✅ Zero references to `ModelName` enum in production code
- ✅ Test suite passes with < 5 failures (unrelated to migration)
- ✅ Linting passes with zero errors
- ✅ Backend starts without errors
- ✅ Basic API endpoints functional
- ✅ Non-LLM build succeeds

---

## Notes for Coders

### Key Differences: load_llm() vs load_agent()

| Aspect | Old `load_llm()` | New `load_agent()` |
|--------|------------------|---------------------|
| Interface | `SupportsStream` protocol | `MidoriAiAgentProtocol` |
| Returns | Custom wrapper object | Framework agent |
| Async | Sync (needs `asyncio.to_thread()`) | Native async |
| Payload | Raw string | `AgentPayload` struct |
| Response | Raw string stream | `AgentResponse` struct |
| Config | Env vars only | Config file + env vars |
| Streaming | Custom `generate_stream()` | Framework `stream()` |

### Common Migration Patterns

#### Pattern 1: Simple Load
```python
# OLD
from llms.loader import load_llm
llm = await asyncio.to_thread(load_llm, model)

# NEW
from llms import load_agent
agent = await load_agent(model=model)
```

#### Pattern 2: With Validation
```python
# OLD
from llms.loader import load_llm, validate_lrm
llm = await asyncio.to_thread(load_llm, model, validate=True)

# NEW
from llms import load_agent, validate_agent
agent = await load_agent(model=model, validate=True)
```

#### Pattern 3: Streaming
```python
# OLD
async for chunk in llm.generate_stream(prompt):
    yield chunk

# NEW
from midori_ai_agent_base import AgentPayload
payload = AgentPayload(
    user_message=prompt,
    thinking_blob="",
    system_context="You are helpful.",
    user_profile={},
    tools_available=[],
    session_id="session",
)
async for chunk in agent.stream(payload):
    yield chunk
```

#### Pattern 4: Test Mocking
```python
# OLD
monkeypatch.setattr("llms.loader.load_llm", fake_loader)

# NEW
monkeypatch.setattr("llms.agent_loader.load_agent", fake_loader)
# OR
monkeypatch.setattr("llms.load_agent", fake_loader)
```

### Debugging Tips
- Check agent framework availability: `python -c "from midori_ai_agent_base import get_agent"`
- Check logger availability: `python -c "from midori_ai_logger import get_logger"`
- View agent config: `python -c "from llms import get_agent_config; print(get_agent_config())"`
- Test agent loading: `python -c "import asyncio; from llms import load_agent; asyncio.run(load_agent())"`

---

## Timeline Estimate

| Phase | Estimated Time | Complexity |
|-------|---------------|------------|
| Phase 1: Pre-Flight | 15-30 min | Low |
| Phase 2: Core Migration | 1-2 hours | High (breaking) |
| Phase 3: Simple Call Sites | 1-2 hours | Low |
| Phase 4: Character Plugins | 2-3 hours | Medium |
| Phase 5: Chat Room | 1 hour | Medium |
| Phase 6: Test Updates | 2-3 hours | Medium |
| Phase 7: Safety.py | 30 min | Low |
| Phase 8: Final Validation | 1 hour | Low |
| **TOTAL** | **9-13 hours** | **High** |

### Recommended Approach
- **Sprint 1 (4-5 hours)**: Phases 1-3 (Core migration + simple updates)
- **Sprint 2 (4-5 hours)**: Phases 4-6 (Plugins + tests)
- **Sprint 3 (1-3 hours)**: Phases 7-8 (Cleanup + validation)

---

## Related Documentation

### Internal References
- [GOAL-midori-ai-agent-framework-migration.md](./GOAL-midori-ai-agent-framework-migration.md) - Overall migration strategy
- [32e92203-migrate-llm-loader.md](./32e92203-migrate-llm-loader.md) - Parent task
- [c0f04e25-update-chat-room.md](./c0f04e25-update-chat-room.md) - Chat room redesign
- [656b2a7e-create-config-support.md](../656b2a7e-create-config-support.md) - Config file support

### External References
- [midori-ai-agent-base docs](https://github.com/Midori-AI-OSS/agents-packages/blob/main/midori-ai-agent-base/docs.md)
- [midori-ai-agent-openai docs](https://github.com/Midori-AI-OSS/agents-packages/blob/main/midori-ai-agent-openai/docs.md)
- [midori-ai-agent-huggingface docs](https://github.com/Midori-AI-OSS/agents-packages/blob/main/midori-ai-agent-huggingface/docs.md)
- [midori-ai-logger docs](https://github.com/Midori-AI-OSS/agents-packages/tree/main/logger)

---

## Change Log

| Date | Author | Changes |
|------|--------|---------|
| 2025-12-20 | Task Master | Initial execution plan created |

---

## Task Master Sign-Off

This execution plan has been reviewed and approved for implementation. Coders assigned to this task should:
1. Read this entire document before starting
2. Follow the phases in order
3. Check off tasks as completed
4. Update this document with any deviations or issues
5. Report progress regularly

**Approved by**: Task Master  
**Date**: 2025-12-20  
**Status**: Ready for implementation
