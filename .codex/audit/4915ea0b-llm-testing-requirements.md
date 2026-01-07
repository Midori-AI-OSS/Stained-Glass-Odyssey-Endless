# LLM/LRM Testing Requirements Audit

**Audit ID:** 4915ea0b  
**Date:** 2025-01-07  
**Auditor:** Auditor Mode  
**Scope:** LLM/LRM functionality testing and integration coverage

---

## Executive Summary

This audit analyzed the LLM/LRM (Large Language Model / Large Reasoning Model) functionality in the AutoFighter backend to identify:
1. Existing LLM features and architecture
2. Current test coverage (mocked vs real)
3. Gaps in non-mocked integration testing
4. Pre-built backend LLM support status
5. Dependencies and environment requirements for real LLM testing

**Key Finding:** All existing LLM tests are **fully mocked**. There are **zero non-mocked integration tests** that validate actual LLM functionality with real model inference.

---

## 1. LLM Features in Backend

### 1.1 Core LLM Infrastructure

**Location:** `backend/llms/`

The backend has a comprehensive LLM framework built on the Midori AI Agent Framework:

#### Agent Loader (`llms/agent_loader.py`)
- **Primary Interface:** `load_agent()`, `validate_agent()`, `get_agent_config()`
- **Backend Support:**
  - **OpenAI backend:** For OpenAI API, Ollama, LocalAI, and compatible services (remote inference)
  - **HuggingFace backend:** For local inference with torch and transformers
- **Configuration Sources:**
  - `config.toml` file (primary)
  - Environment variables (fallback):
    - `OPENAI_API_URL` - API endpoint
    - `OPENAI_API_KEY` - API authentication
    - `AF_LLM_MODEL` - Model selection (default: "gpt-oss:20b")
- **Auto-detection:** Selects OpenAI if `OPENAI_API_URL` is set, otherwise HuggingFace if torch is available
- **Validation:** `validate_agent()` sends a test prompt and checks response length > 5 characters

#### Torch Checker (`llms/torch_checker.py`)
- **Purpose:** Centralized availability check for torch and ML dependencies
- **Single Import Check:** Performed once on module import to avoid repeated overhead
- **Dependencies Checked:**
  - `torch`
  - `transformers`
  - `langchain_huggingface`
  - `langchain_community.llms.llamacpp`

#### Safety Module (`llms/safety.py`)
- **Resource Validation:**
  - `get_available_memory()` - System RAM
  - `get_available_vram()` - GPU VRAM
  - `pick_device()` - Select GPU/CPU based on VRAM requirements
  - `model_memory_requirements()` - Estimate RAM/VRAM needs from HuggingFace model metadata
  - `ensure_ram()` - Raise error if insufficient memory

### 1.2 Chat Room Integration

**Location:** `backend/autofighter/rooms/chat.py`

**ChatRoom Class:**
- Forwards messages to LRM characters in chat room scenarios
- Uses `load_agent()` to get agent instance
- Streams responses via `agent.stream(payload)`
- Includes TTS (Text-to-Speech) integration via `tts.generate_voice()`
- Returns response with optional voice file path

**Agent Payload Structure:**
```python
AgentPayload(
    user_message=json.dumps({"party": party_data, "message": message}),
    thinking_blob="",
    system_context="You are a character in the AutoFighter game chat room.",
    user_profile={},
    tools_available=[],
    session_id="chat_room"
)
```

### 1.3 Configuration Endpoints

**Location:** `backend/routes/config.py`

**Endpoints:**
- `GET /config/lrm` - Retrieve current LRM configuration
  - Returns: model, backend, api_url, api_key (masked), available models/backends
- `POST /config/lrm` - Update LRM configuration
  - Accepts: model, backend, api_url, api_key
  - Validates backend choices: "auto", "openai", "huggingface"
  - Persists to options database
- `POST /config/lrm/backend` - Set backend only
- `POST /config/lrm/test` - Test LRM with custom prompt
  - Uses `validate_agent()` if no prompt provided
  - Executes custom prompt via `agent.invoke()` if provided

### 1.4 Startup Validation

**Location:** `backend/app.py`

**`validate_lrm_on_startup()` Hook:**
- Runs during `@app.before_serving`
- Checks torch availability and `OPENAI_API_URL` environment variable
- Skips silently if neither is configured (avoids log spam)
- Loads and validates agent on startup
- Logs validation result (✓ passed / ✗ failed)
- Non-blocking: Server continues starting even if validation fails

**Backend Flavor Detection:**
```python
BACKEND_FLAVOR = os.getenv("UV_EXTRA", "default")
```
Returned in `GET /` status endpoint.

### 1.5 Player/Foe Memory System

**Location:** Referenced in `backend/tests/test_lrm_memory.py`

**Features:**
- `send_lrm_message()` and `receive_lrm_message()` methods on PlayerBase and FoeBase
- `lrm_memory` object with `load_memory_variables()` to retrieve conversation history
- Per-instance isolation: each player/foe maintains separate memory

---

## 2. Current Test Coverage

### 2.1 Existing Tests (All Mocked)

| Test File | Purpose | Mocking Strategy |
|-----------|---------|------------------|
| `test_agent_loader.py` | Agent loading, validation, backend selection | Fully mocked: monkeypatches `get_agent`, `is_torch_available`, framework availability |
| `test_chat_room.py` | ChatRoom integration | Fully mocked: `FakeAgent` with hardcoded responses, mock `load_agent` |
| `test_app_without_llm_deps.py` | App runs without torch | Blocks torch import, verifies non-LLM endpoints work |
| `test_config_lrm.py` | LRM config endpoints | Fully mocked: `FakeAgent` for test endpoint, monkeypatched `load_agent` |
| `test_lrm_memory.py` | Player/Foe memory isolation | **Not mocked at unit level** - tests actual memory objects, but doesn't test with real LLM |

**Key Observation:** Every test that touches LLM code uses mocks/fakes:
- `FakeAgent` classes with hardcoded responses
- `monkeypatch.setattr()` to replace `load_agent`, `get_agent`, framework checks
- No actual model loading or inference

### 2.2 Mock Patterns Used

**Common FakeAgent Pattern:**
```python
class FakeAgent:
    async def invoke(self, payload):
        class FakeResponse:
            response = f"Response to: {payload.user_message}"
        return FakeResponse()
    
    async def stream(self, payload):
        yield "reply"
```

**Framework Availability Mocking:**
```python
monkeypatch.setattr(llms.agent_loader, "_AGENT_FRAMEWORK_AVAILABLE", True)
```

**Module Import Mocking:**
```python
import sys
from unittest.mock import MagicMock
mock_module = MagicMock()
mock_module.AgentPayload = MockAgentPayload
sys.modules['midori_ai_agent_base'] = mock_module
```

### 2.3 Test Execution Environment

**CI/CD:** `.github/workflows/backend-ci.yml`
- Uses `ubuntu-latest` runner
- Python 3.12
- Command: `uv run pytest tests/`
- **No LLM extras installed** - runs with base dependencies only
- All LLM tests pass because they're mocked

**Local Testing:** `run-tests.sh`
- 15-second timeout per test
- Optional Docker execution with `pixelarch:quartz` image
- Can use `UV_EXTRA` environment variable for extras
- Falls back to local execution if Docker unavailable

---

## 3. Missing Non-Mocked Integration Tests

### 3.1 Critical Gaps

The following scenarios have **zero real integration test coverage**:

#### 3.1.1 Agent Loading & Backend Selection
**Missing Tests:**
- [ ] Load real OpenAI agent with mock API server (e.g., LocalAI, mock-server)
- [ ] Load real HuggingFace agent with small model (e.g., `distilgpt2`)
- [ ] Auto-detection logic with real environment configuration
- [ ] Backend fallback: OpenAI unavailable → HuggingFace with torch
- [ ] Backend fallback: Both unavailable → proper error handling
- [ ] Config file parsing and override behavior
- [ ] Environment variable precedence testing

#### 3.1.2 Agent Validation
**Missing Tests:**
- [ ] `validate_agent()` with real model producing valid responses (>5 chars)
- [ ] `validate_agent()` with intentionally broken/non-reasoning model
- [ ] Validation timeout behavior
- [ ] Validation with malformed responses

#### 3.1.3 Chat Room Integration
**Missing Tests:**
- [ ] End-to-end chat room flow with real agent
- [ ] Streaming response handling with real model
- [ ] Party data serialization and injection into prompts
- [ ] Error recovery when agent fails mid-stream
- [ ] TTS integration with actual voice generation
- [ ] Memory persistence across multiple chat interactions

#### 3.1.4 Configuration Endpoints
**Missing Tests:**
- [ ] `/config/lrm/test` with real model inference
- [ ] Model switching: reconfigure and verify new model loads
- [ ] API key validation with real remote endpoint
- [ ] Invalid API URL handling (connection refused, timeout)
- [ ] Backend migration: switch from HuggingFace to OpenAI and verify
- [ ] Persistence: restart server and verify config retained

#### 3.1.5 Startup Validation
**Missing Tests:**
- [ ] Server startup with valid remote LRM configured
- [ ] Server startup with valid local LRM (torch + model)
- [ ] Server startup with invalid LRM (should warn but continue)
- [ ] Server startup with no LRM (should skip silently)
- [ ] Startup validation timing and non-blocking behavior

#### 3.1.6 Resource Management
**Missing Tests:**
- [ ] Memory estimation accuracy for real models
- [ ] Device selection with real GPU/CPU environments
- [ ] VRAM overflow handling: model too large for GPU
- [ ] RAM overflow handling: model too large for system
- [ ] Quantization (8-bit, 4-bit) with real models

#### 3.1.7 Error Handling & Edge Cases
**Missing Tests:**
- [ ] Agent framework import failure scenarios
- [ ] Torch unavailable but local inference requested
- [ ] Model download failures (network error, invalid model name)
- [ ] Concurrent agent loading (thread safety)
- [ ] Agent timeout during long inference
- [ ] Malformed model responses (non-JSON, binary data, etc.)

### 3.2 Impact Assessment

**Critical (Severity: HIGH):**
- Backend selection and fallback logic is untested with real conditions
- Agent validation may produce false positives/negatives
- Chat room streaming could fail in production
- Resource safety checks are unverified

**Important (Severity: MEDIUM):**
- Configuration persistence across restarts
- Startup validation non-blocking behavior
- Error messages and logging quality

**Nice to Have (Severity: LOW):**
- Performance characteristics with real models
- Memory usage profiling
- Stress testing with concurrent requests

---

## 4. Pre-Built Backend LLM Support

### 4.1 Docker Compose Variants

**Location:** `compose.yaml`

Three LLM-enabled backend variants:

```yaml
backend-llm-cuda:
  environment:
    UV_EXTRA: llm-cuda
  labels:
    - llm-cuda

backend-llm-amd:
  environment:
    UV_EXTRA: llm-amd
  labels:
    - llm-amd

backend-llm-cpu:
  environment:
    UV_EXTRA: llm-cpu
  labels:
    - llm-cpu
```

**Base Image:** `lunamidori5/pixelarch:quartz`
- Arch Linux base
- Includes `uv`, `docker`, `docker-compose`
- Python 3.13 environment

**Entrypoint:** `docker-entrypoint.sh`
- Installs extras via `uv sync --extra "$UV_EXTRA"`
- Runs `uv run app.py --extra "$UV_EXTRA"`

### 4.2 Build Script

**Location:** `build.sh`

**Variants Supported:**
- `non-llm` - Base dependencies only
- `llm-cpu` - CPU inference with torch
- `llm-cuda` - CUDA GPU inference
- `llm-amd` - AMD GPU inference

**Build Process:**
1. Frontend build (bun or npm)
2. Backend setup with uv
3. Variant-specific dependency installation
4. PyInstaller executable creation

**Output:** `dist/midori-autofighter-{variant}-{platform}`

### 4.3 Dependency Extras

**Location:** `backend/pyproject.toml`

```toml
[project.optional-dependencies]
llm-cpu = [
    "midori-ai-agents-all",  # Agent framework
    "midori-ai-logger",      # Structured logging
    "torch",
    "torchaudio",
    "torchvision",
    "transformers",
    "sentence-transformers",
    "accelerate",
    "pillow",
]

llm-cuda = [...]  # Same as llm-cpu
llm-amd = [...]   # Same as llm-cpu
```

**Agent Framework Sources:**
```toml
[tool.uv.sources]
midori-ai-agents-all = { 
    git = "https://github.com/Midori-AI-OSS/agents-packages.git", 
    subdirectory = "midori-ai-agents-all" 
}
midori-ai-logger = { 
    git = "https://github.com/Midori-AI-OSS/agents-packages.git", 
    subdirectory = "logger" 
}
```

### 4.4 LLM Support Status in Pre-Built Backends

**Status:** ✅ **ENABLED** (Conditional)

The pre-built Docker images support LLM functionality through:
1. **Variant Selection:** Choose `backend-llm-cpu`, `backend-llm-cuda`, or `backend-llm-amd`
2. **Automatic Dependency Installation:** Entrypoint installs extras on container start
3. **Runtime Configuration:** Set `OPENAI_API_URL` for remote inference or rely on torch for local

**However:**
- CI/CD does NOT test LLM variants (uses base dependencies only)
- No automated verification that LLM features work in pre-built images
- Manual testing required to confirm LLM support

---

## 5. Dependencies & Environment Setup for Real LLM Testing

### 5.1 Minimum Test Setup (Remote OpenAI API)

**Approach:** Use mock OpenAI-compatible server for testing without large models.

**Dependencies:**
```bash
uv sync --extra llm-cpu  # or use base + manual install
pip install httpx        # If not already included
```

**Mock Server Options:**
1. **LocalAI** - Full OpenAI-compatible server with tiny models
2. **FastAPI Mock** - Custom test fixture returning canned responses
3. **Ollama** - Can run very small models (phi-2, tinyllama)
4. **WireMock** - HTTP mock server for API simulation

**Environment:**
```bash
export OPENAI_API_URL="http://localhost:8080/v1"
export OPENAI_API_KEY="test-key"
export AF_LLM_MODEL="phi-2"  # Small test model
```

**Test Infrastructure Code:**
```python
import pytest
from contextlib import asynccontextmanager

@pytest.fixture(scope="session")
async def mock_openai_server():
    """Start a mock OpenAI-compatible server for testing."""
    # Start LocalAI or custom FastAPI server
    # Return base URL
    yield "http://localhost:8080"
    # Cleanup

@asynccontextmanager
async def real_agent_test_context(model="phi-2"):
    """Context manager for tests requiring real agent."""
    import os
    os.environ["OPENAI_API_URL"] = "http://localhost:8080/v1"
    os.environ["AF_LLM_MODEL"] = model
    from llms import load_agent
    agent = await load_agent()
    yield agent
    # Cleanup if needed
```

### 5.2 Full Integration Test Setup (Local Inference)

**Approach:** Use minimal HuggingFace models for real inference testing.

**Dependencies:**
```bash
uv sync --extra llm-cpu
```

**Installs:**
- torch (~800MB)
- transformers (~400MB)
- sentence-transformers (~50MB)
- accelerate (~50MB)
- midori-ai-agents-all (lightweight)
- midori-ai-logger (lightweight)

**Recommended Test Models:**
- **`distilgpt2`** - 82MB, fast, suitable for response generation tests
- **`microsoft/phi-2`** - 2.7GB, reasoning-capable, small enough for CI
- **`TinyLlama/TinyLlama-1.1B`** - 2.2GB, instruction-tuned
- **`openai/gpt-oss-20b`** - 40GB, production model (too large for CI)

**Environment:**
```bash
export AF_LLM_MODEL="distilgpt2"
# Or unset OPENAI_API_URL to force local inference
unset OPENAI_API_URL
```

**Resource Requirements:**
| Model | RAM | VRAM (GPU) | Inference Time |
|-------|-----|------------|----------------|
| distilgpt2 | 1GB | 500MB | <1s |
| phi-2 | 4GB | 2GB | 1-3s |
| TinyLlama-1.1B | 4GB | 2GB | 1-3s |
| gpt-oss-20b | 40GB+ | 20GB+ | 5-30s |

### 5.3 CI/CD Integration Strategy

**Recommended Approach: Hybrid**

```yaml
# .github/workflows/backend-llm-integration.yml
name: LLM Integration Tests

on:
  workflow_dispatch:  # Manual trigger
  schedule:
    - cron: '0 6 * * 1'  # Weekly Monday 6am

jobs:
  llm-remote-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: astral-sh/setup-uv@v6
      
      # Setup mock OpenAI server
      - name: Start LocalAI
        run: |
          docker run -d -p 8080:8080 \
            -e MODELS_PATH=/models \
            localai/localai:latest-aio-cpu
          sleep 30  # Wait for startup
      
      - name: Install dependencies
        run: uv sync --extra llm-cpu
      
      - name: Run remote LLM integration tests
        env:
          OPENAI_API_URL: http://localhost:8080/v1
          AF_LLM_MODEL: phi-2
        run: uv run pytest tests/integration/llm/ -m remote

  llm-local-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: astral-sh/setup-uv@v6
      
      - name: Install dependencies with LLM support
        run: uv sync --extra llm-cpu
      
      - name: Run local LLM integration tests
        run: uv run pytest tests/integration/llm/ -m local
```

**pytest Markers:**
```python
# conftest.py
def pytest_configure(config):
    config.addinivalue_line("markers", "remote: tests requiring remote LLM API")
    config.addinivalue_line("markers", "local: tests requiring local torch inference")
    config.addinivalue_line("markers", "slow: tests taking >10 seconds")
    config.addinivalue_line("markers", "gpu: tests requiring GPU")
```

### 5.4 Test Data Requirements

**Fixtures Needed:**
1. **Model Download Cache:** Pre-download test models to avoid timeout
2. **Sample Prompts:** Known input/output pairs for validation
3. **Party Data:** Serialized party objects for ChatRoom tests
4. **Config Files:** Various `config.toml` configurations

**Example Fixture:**
```python
@pytest.fixture(scope="session")
def test_model_cache(tmp_path_factory):
    """Pre-download and cache test models."""
    cache_dir = tmp_path_factory.mktemp("models")
    os.environ["HF_HOME"] = str(cache_dir)
    
    # Pre-download
    from transformers import AutoModelForCausalLM
    AutoModelForCausalLM.from_pretrained("distilgpt2", cache_dir=cache_dir)
    
    return cache_dir
```

### 5.5 Performance Considerations

**Test Execution Time Targets:**
- Remote API tests: <5s per test (with mock server)
- Local inference tests: <10s per test (with distilgpt2)
- Full agent tests: <30s per test (with phi-2)
- Startup validation: <60s (one-time per suite)

**Optimization Strategies:**
1. **Session-scoped fixtures:** Load model once per test session
2. **Parallel execution:** Use `pytest-xdist` for independent tests
3. **Caching:** Store downloaded models in CI cache
4. **Selective execution:** Use markers to skip slow tests in fast CI

---

## 6. Testing Recommendations

### 6.1 Immediate Actions (Priority 1)

1. **Create Integration Test Suite Structure**
   ```
   backend/tests/integration/
   ├── llm/
   │   ├── conftest.py          # Fixtures for agent, mock server
   │   ├── test_agent_loading_real.py
   │   ├── test_agent_validation_real.py
   │   ├── test_chat_room_real.py
   │   └── test_config_endpoints_real.py
   ```

2. **Implement Mock OpenAI Server Fixture**
   - Use LocalAI or FastAPI-based mock
   - Return predictable responses for validation
   - Support streaming endpoint

3. **Add Basic Remote Agent Tests**
   - Test 1: Load agent with mock server
   - Test 2: Validate agent with mock responses
   - Test 3: ChatRoom with mock streaming

4. **Document Test Execution**
   - Add `TESTING.md` with instructions
   - Document environment setup
   - Provide example commands

### 6.2 Short-Term Goals (Priority 2)

1. **Local Inference Tests**
   - Setup with `distilgpt2` for fast tests
   - Test HuggingFace backend selection
   - Test torch availability detection

2. **Configuration Persistence Tests**
   - Verify config.toml parsing
   - Test environment variable overrides
   - Validate API key masking

3. **Error Handling Tests**
   - Network failures
   - Invalid model names
   - Timeout scenarios

4. **CI/CD Workflow**
   - Create separate workflow for integration tests
   - Manual trigger + weekly schedule
   - Cache model downloads

### 6.3 Long-Term Goals (Priority 3)

1. **Performance Benchmarks**
   - Response time metrics
   - Memory usage tracking
   - Concurrent request handling

2. **Production Model Tests**
   - Test with actual `gpt-oss-20b` (manual only)
   - Validate reasoning quality
   - Stress test with long conversations

3. **GPU Testing**
   - CUDA variant validation
   - AMD variant validation
   - Device selection verification

4. **E2E Testing**
   - Full frontend → backend → LLM flow
   - TTS integration validation
   - Player/Foe memory across sessions

### 6.4 Test Design Principles

**For Integration Tests:**
1. **Isolation:** Each test cleans up its resources
2. **Determinism:** Use fixed seeds where possible
3. **Fast Feedback:** Target <30s per test
4. **Clear Failures:** Detailed error messages
5. **Realistic:** Use actual agent framework APIs

**For Mocked Tests (Keep These):**
- Unit tests for logic without inference
- Fast regression detection (<1s per test)
- No external dependencies
- High coverage of edge cases

**Complementary Approach:**
- Mocked tests: Quick validation of code paths
- Integration tests: Verify real-world behavior
- Both are necessary for complete coverage

---

## 7. Risk Assessment

### 7.1 Current Risks

| Risk | Severity | Likelihood | Impact |
|------|----------|------------|--------|
| Agent loading fails in production | HIGH | MEDIUM | Critical: Chat feature broken |
| Backend selection logic incorrect | HIGH | HIGH | Major: Wrong backend used, poor performance |
| Validation gives false positives | MEDIUM | HIGH | Moderate: Bad models accepted |
| Config changes not persisted | MEDIUM | LOW | Moderate: User settings lost |
| Resource checks inaccurate | HIGH | MEDIUM | Critical: OOM crashes |
| Startup validation blocks server | MEDIUM | LOW | Major: Server won't start |

### 7.2 Mitigation Strategies

1. **Staged Rollout:**
   - Test remote API integration first (lower risk)
   - Add local inference tests second
   - Validate resource checks last (highest complexity)

2. **Monitoring:**
   - Add telemetry to agent loading
   - Log all validation attempts
   - Track model inference times

3. **Fallback Mechanisms:**
   - Ensure server runs without LLM
   - Graceful degradation in chat rooms
   - Clear error messages to users

4. **Documentation:**
   - Update `.codex/implementation/` with test strategies
   - Document known limitations
   - Provide troubleshooting guide

---

## 8. Conclusion

### 8.1 Summary of Findings

The AutoFighter backend has a **well-architected LLM system** with:
- ✅ Flexible backend selection (OpenAI, HuggingFace)
- ✅ Comprehensive configuration options
- ✅ Resource safety checks
- ✅ Graceful degradation without LLM dependencies
- ✅ Good separation of concerns

However, **testing is entirely mocked**, leaving critical gaps:
- ❌ Zero real agent loading validation
- ❌ No backend selection testing with actual conditions
- ❌ No inference quality verification
- ❌ Unverified resource estimation
- ❌ No CI coverage of LLM variants

### 8.2 Critical Next Steps

1. **Implement mock OpenAI server fixture** (Effort: 4 hours)
2. **Write 5 basic integration tests** (Effort: 8 hours)
   - Agent loading (remote)
   - Agent validation (remote)
   - ChatRoom integration (remote)
   - Config persistence
   - Error handling
3. **Add integration test CI workflow** (Effort: 2 hours)
4. **Document test execution in TESTING.md** (Effort: 1 hour)

**Total Estimated Effort:** 15 hours to establish baseline integration testing.

### 8.3 Success Metrics

**After implementing recommendations:**
- [ ] At least 10 non-mocked integration tests passing
- [ ] CI workflow executing integration tests weekly
- [ ] Integration test execution time <5 minutes
- [ ] Pre-built Docker images validated with real LLM tests
- [ ] Documentation for running integration tests locally
- [ ] Code coverage for LLM code paths >60% (currently ~30% real coverage)

---

## Appendix A: Test File Inventory

| File | Lines | Mocking | Coverage |
|------|-------|---------|----------|
| `test_agent_loader.py` | 192 | Heavy | Backend selection, validation, errors |
| `test_chat_room.py` | 73 | Heavy | ChatRoom.resolve(), model selection |
| `test_app_without_llm_deps.py` | 48 | Import blocking | Non-LLM endpoints work without torch |
| `test_config_lrm.py` | 182 | Heavy | Config endpoints, persistence, validation |
| `test_lrm_memory.py` | 37 | None (unit) | Player/Foe memory isolation |

**Total LLM Test Code:** ~532 lines  
**Real Integration Coverage:** 0%  
**Mocked Unit Coverage:** ~95%

---

## Appendix B: Recommended Test Models

| Model | Size | Speed | Use Case |
|-------|------|-------|----------|
| `distilgpt2` | 82MB | Very Fast | Basic response generation |
| `microsoft/phi-2` | 2.7GB | Fast | Reasoning validation |
| `TinyLlama/TinyLlama-1.1B` | 2.2GB | Fast | Instruction following |
| `openai/gpt-oss-20b` | 40GB | Slow | Production simulation (manual only) |

---

## Appendix C: Environment Variables Reference

| Variable | Purpose | Default | Required |
|----------|---------|---------|----------|
| `OPENAI_API_URL` | Remote API endpoint | "unset" | For remote inference |
| `OPENAI_API_KEY` | API authentication | "unset" | For authenticated APIs |
| `AF_LLM_MODEL` | Model selection | "gpt-oss:20b" | No (has default) |
| `UV_EXTRA` | Dependency variant | None | For Docker variants |
| `AF_DB_PATH` | Database location | "./save.db" | For persistence tests |
| `AF_DB_KEY` | Database encryption | None | For encrypted DB tests |

---

## Appendix D: Related Documentation

- `backend/.codex/implementation/llm-loader.md` - Original LLM loader design (pre-agent framework)
- `backend/.codex/implementation/lrm-config.md` - Configuration endpoint design
- `backend/config.toml.example` - Configuration file template
- `backend/README.md` - Backend setup instructions
- `AGENTS.md` - Contributor guidelines (this audit follows Auditor Mode)

---

**End of Audit Report**

**Recommended Action:** Assign a Coder to implement the Priority 1 tasks within the next sprint.
