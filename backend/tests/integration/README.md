# LLM Real Integration Tests

This directory contains **non-mocked** integration tests for the LLM functionality in the AutoFighter backend. These tests validate actual LLM behavior with real model inference.

## Purpose

Unlike the unit tests in `backend/tests/` which use mocked agents, these integration tests:

- ✅ Load **real models** (HuggingFace, OpenAI-compatible APIs)
- ✅ Perform **actual inference** with model completion
- ✅ Validate **real-world behavior** of the LLM system
- ✅ Test **error handling** with actual failure scenarios
- ✅ Verify **configuration** and **backend selection** logic

## Test Coverage

The `test_llm_real.py` suite includes:

1. **Agent Loading** - Real HuggingFace backend with distilgpt2
2. **Chat Completion** - Actual model inference and response generation
3. **Agent Validation** - Real validation with model responses
4. **Error Handling** - Invalid model names and missing dependencies
5. **Backend Auto-Detection** - Environment-based backend selection
6. **Configuration Loading** - Config file parsing and overrides
7. **Concurrent Loading** - Thread-safe agent loading
8. **Streaming Responses** - Real streaming API testing (if supported)
9. **Memory Cleanup** - Agent lifecycle and resource management
10. **E2E Conversation** - Multi-turn conversation flows

## Requirements

### Minimum (Remote API Testing)
```bash
# Install LLM dependencies (CPU version)
uv sync --extra llm-cpu

# Set up mock OpenAI server (optional)
export OPENAI_API_URL="http://localhost:8080/v1"
export OPENAI_API_KEY="test-key"
```

### Full (Local Inference Testing)
```bash
# Install LLM dependencies
uv sync --extra llm-cpu

# Tests will download models on first run
# Models are cached in HF_HOME directory
```

### Installed Dependencies
- `torch` - PyTorch for local inference
- `transformers` - HuggingFace transformers
- `midori-ai-agents-all` - Midori AI Agent Framework
- `sentence-transformers` - Embeddings (optional)
- `accelerate` - Fast inference (optional)

## Test Model

Tests use **distilgpt2** (82MB) by default for speed:

- **Size**: 82MB (small and fast)
- **Speed**: <1s inference on CPU
- **Cache**: Downloads once, cached for future runs
- **Total Time**: <30 seconds for all tests

Alternative models can be configured via `TEST_MODEL` constant in `test_llm_real.py`.

## Running Tests

### Basic Execution
```bash
# Run all integration tests (skips if dependencies not available)
uv run pytest tests/integration/test_llm_real.py -v

# Run with output visible
uv run pytest tests/integration/test_llm_real.py -v -s

# Run specific test
uv run pytest tests/integration/test_llm_real.py::test_chat_completion_real -v -s
```

### With LLM Dependencies
```bash
# Install dependencies first
cd backend
uv sync --extra llm-cpu

# Run tests (will download model on first run)
uv run pytest tests/integration/test_llm_real.py -v -s

# Subsequent runs use cached model (much faster)
uv run pytest tests/integration/test_llm_real.py -v
```

### Skip Behavior
If LLM dependencies are **not installed**, all tests will automatically **skip**:

```
tests/integration/test_llm_real.py::test_load_agent_huggingface_real SKIPPED
tests/integration/test_llm_real.py::test_chat_completion_real SKIPPED
...
Reason: LLM dependencies not installed. Run: uv sync --extra llm-cpu
```

This allows the main test suite to run without LLM dependencies while providing real integration testing when needed.

## Test Markers

Tests use pytest markers for organization:

```python
# Mark test as requiring real LLM (auto-applied by module-level pytestmark)
@pytest.mark.llm_real

# Mark slow tests (>10 seconds)
@pytest.mark.slow
```

Run specific marker groups:
```bash
# Run only LLM real tests
uv run pytest -m llm_real -v

# Skip slow tests
uv run pytest -m "not slow" tests/integration/
```

## Environment Variables

Configure LLM behavior via environment variables:

| Variable | Purpose | Default | Example |
|----------|---------|---------|---------|
| `AF_LLM_MODEL` | Model to use | `gpt-oss:20b` | `distilgpt2` |
| `OPENAI_API_URL` | Remote API endpoint | unset | `http://localhost:8080/v1` |
| `OPENAI_API_KEY` | API authentication | unset | `sk-test-key` |
| `HF_HOME` | HuggingFace cache | `~/.cache/huggingface` | `/tmp/hf_cache` |

## CI/CD Integration

These tests are **not** run in the standard CI/CD workflow because:

1. Model downloads are too large for fast CI
2. Inference is too slow for every PR
3. GPU may not be available in CI runners

### Recommended CI Strategy

Create a separate workflow for weekly integration testing:

```yaml
# .github/workflows/backend-llm-integration.yml
name: LLM Integration Tests

on:
  workflow_dispatch:  # Manual trigger
  schedule:
    - cron: '0 6 * * 1'  # Weekly Monday 6am

jobs:
  llm-integration:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: astral-sh/setup-uv@v6
      
      - name: Install LLM dependencies
        run: |
          cd backend
          uv sync --extra llm-cpu
      
      - name: Run LLM integration tests
        run: |
          cd backend
          uv run pytest tests/integration/test_llm_real.py -v -s
```

## Performance

Expected execution times with distilgpt2 on CPU:

| Test | Time |
|------|------|
| Agent loading | ~5s (first run with download: ~30s) |
| Chat completion | ~2s |
| Validation | ~2s |
| Error handling | <1s |
| Backend detection | ~3s |
| Config loading | <1s |
| Concurrent loading | ~8s |
| Streaming | ~3s |
| Memory cleanup | ~5s |
| E2E conversation | ~5s |
| **Total** | **~30s** |

First run with model download: ~60s

## Troubleshooting

### Tests Skip Automatically
**Problem**: All tests show `SKIPPED` status.

**Solution**: Install LLM dependencies:
```bash
cd backend
uv sync --extra llm-cpu
```

### Model Download Fails
**Problem**: `Failed to download test model: ...`

**Solution**: Check internet connection and HuggingFace availability:
```bash
# Test HuggingFace connection
curl -I https://huggingface.co

# Clear cache and retry
rm -rf ~/.cache/huggingface/hub
uv run pytest tests/integration/test_llm_real.py -v -s
```

### Out of Memory Errors
**Problem**: `RuntimeError: CUDA out of memory` or similar

**Solution**: Use CPU-only inference or smaller model:
```bash
# Force CPU usage
export CUDA_VISIBLE_DEVICES=""

# Or use smaller model
# Edit test_llm_real.py: TEST_MODEL = "distilgpt2"
```

### Tests Are Too Slow
**Problem**: Tests take too long on your machine.

**Solution**: Use an even smaller model or skip slow tests:
```bash
# Skip slow tests
uv run pytest tests/integration/ -m "not slow" -v

# Or edit TEST_MODEL in test_llm_real.py to use smaller model
```

## Development Guidelines

When adding new LLM integration tests:

1. **Keep tests fast** - Use `distilgpt2` or similar small models
2. **Make them skippable** - Use the module-level `pytestmark` pattern
3. **No mocking** - These are real integration tests
4. **Document clearly** - Explain what real behavior is being validated
5. **Handle errors gracefully** - Tests should fail with clear messages
6. **Clean up resources** - Use fixtures for setup/teardown
7. **Use session fixtures** - Share expensive setup (model loading) across tests

### Example Test Pattern
```python
@pytest.mark.asyncio
async def test_new_llm_feature(test_model_cache, clean_env):
    """Test description explaining REAL behavior validated.
    
    This is a REAL test - explain what's not mocked.
    
    Validates:
        - Specific real-world behavior 1
        - Specific real-world behavior 2
    """
    os.environ["AF_LLM_MODEL"] = TEST_MODEL
    
    # Load real agent (no mocking!)
    agent = await load_agent(...)
    
    # Perform REAL operation
    result = await agent.invoke(...)
    
    # Validate real behavior
    assert result is not None
    print(f"✓ Real test passed with result: {result}")
```

## Related Files

- `backend/llms/agent_loader.py` - Agent loading implementation
- `backend/tests/test_agent_loader.py` - Mocked unit tests
- `backend/tests/test_chat_room.py` - Mocked chat room tests
- `.codex/audit/4915ea0b-llm-testing-requirements.md` - Audit findings

## Contributing

When adding new LLM functionality:

1. Add **mocked unit tests** to `backend/tests/` for fast regression detection
2. Add **real integration tests** to `backend/tests/integration/` for validation
3. Document both test types clearly
4. Ensure integration tests skip gracefully without dependencies

Both test types are necessary for complete coverage:
- **Mocked tests**: Fast, no dependencies, high code coverage
- **Integration tests**: Slow, real dependencies, validates actual behavior

---

**Remember**: These tests use REAL models with NO MOCKING. They validate actual LLM functionality.
