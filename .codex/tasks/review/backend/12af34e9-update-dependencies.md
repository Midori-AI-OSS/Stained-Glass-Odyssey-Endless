# Update Dependencies for Midori AI Agent Framework

## Task ID
`12af34e9-update-dependencies`

## Priority
High

## Status
WIP

## Description
Update backend dependencies to use the Midori AI Agent Framework meta-package (`midori-ai-agents-all`) instead of individual langchain, openai, and other LLM-related packages. This is the foundation for all other migration tasks.

## Context
Currently, `backend/pyproject.toml` includes many individual packages for LLM support:
- `openai`, `openai-agents`
- `langchain-core`, `langchain-openai`, `langchain-ollama`, `langchain-localai`, `langchain-community`, `langchain-chroma`, `langchain-huggingface`, `langchain-text-splitters`
- `transformers`, `sentence-transformers`, `accelerate`
- `torch`, `torchaudio`, `torchvision`

The Midori AI Agent Framework provides a meta-package that bundles all necessary dependencies in a standardized way.

## Rationale
- **Simplified Management**: One meta-package instead of 10+ individual packages
- **Version Compatibility**: Framework ensures all packages work together
- **Easier Updates**: Update framework version instead of many packages
- **Reduced Conflicts**: Framework handles dependency resolution
- **Future-Proof**: New framework features automatically available
- **Breaking Changes**: Intentionally breaking old code to find and fix issues faster

## Objectives
1. Add `midori-ai-agents-all` and `midori-ai-logger` packages to dependencies
2. Remove ALL old LLM packages (breaking change)
3. Keep essential packages (torch, transformers) for local model support
4. **BREAK backward compatibility** - remove all old imports and code
5. Use `uv add` to install dependencies properly

## Implementation Steps

### Step 1: Review Current Dependencies
Check current `backend/pyproject.toml`:
```bash
cat backend/pyproject.toml | grep -A 30 "llm-cpu"
```

Document which packages are:
- Provided by `midori-ai-agents-all`
- Still needed (torch, transformers for local models)
- No longer needed

### Step 2: Install Dependencies Using uv add

Use `uv add` to properly install the agent framework:

```bash
cd backend

# Add the agent framework meta-package
uv add "git+https://github.com/Midori-AI-OSS/agents-packages.git#subdirectory=midori-ai-agents-all"

# Add the logger package
uv add "git+https://github.com/Midori-AI-OSS/agents-packages.git#subdirectory=logger"
```

Then manually update `backend/pyproject.toml` optional dependencies:

```toml
[project.optional-dependencies]
llm-cpu = [
    # Core LLM framework and logger
    "midori-ai-agents-all @ git+https://github.com/Midori-AI-OSS/agents-packages.git#subdirectory=midori-ai-agents-all",
    "midori-ai-logger @ git+https://github.com/Midori-AI-OSS/agents-packages.git#subdirectory=logger",
    
    # Still needed for local model support
    "torch",
    "torchaudio", 
    "torchvision",
    "transformers",
    "sentence-transformers",
    "accelerate",
    
    # TTS support (if still needed)
    "chatterbox-tts",
    "pillow",
]
```

**REMOVE** these completely (breaking change):
- `openai`
- `openai-agents`
- `langgraph`
- `langchain-core`
- `langchain-openai`
- `langchain-ollama`
- `langchain-localai`
- `langchain-community`
- `langchain-chroma`
- `langchain-huggingface`
- `langchain-text-splitters`

### Step 3: Update Lock File
Regenerate the lock file:
```bash
cd backend
uv lock --upgrade
```

### Step 4: Verify Installation
Test that the package installs correctly:
```bash
cd backend
uv sync --extra llm-cpu
```

Check that midori-ai-agents-all is installed:
```bash
uv pip list | grep midori
```

Should see:
- midori-ai-agent-base
- midori-ai-agent-context-manager
- midori-ai-agent-huggingface
- midori-ai-agent-langchain
- midori-ai-agent-openai
- midori-ai-agents-all
- And other midori-ai packages

### Step 5: Test Imports (Framework Verification)
Create a test script to verify NEW framework imports work:
```python
# Test NEW framework imports (should work)
from midori_ai_agent_base import MidoriAiAgentProtocol, AgentPayload, AgentResponse
from midori_ai_agent_base import get_agent, get_agent_from_config
from midori_ai_agent_openai import OpenAIAgentsAdapter
from midori_ai_agent_huggingface import HuggingFaceLocalAgent
from midori_ai_logger import get_logger

log = get_logger(__name__)
log.info("New agent framework imports successful!")

# Note: The meta package (midori-ai-agents-all) includes openai and some
# langchain packages as dependencies, so those imports will still work.
# The breaking change is in the API - old code using load_llm() will break,
# not the imports themselves.
```

Run test:
```bash
cd backend
uv run python test_imports.py
```

**Expected**: New framework imports work. Note that openai and some langchain packages
are included by the meta package, so checking import failures is not the right test.
The breaking change is at the API level (load_llm vs load_agent).

### Step 6: Update Build Configuration
Check if build scripts reference specific packages:
```bash
grep -r "langchain\|openai-agents" build/ packaging/
```

Update any hardcoded package references in:
- `build.sh`
- PyInstaller spec files
- Dockerfile configurations

### Step 7: Verify GPU/AMD Extras
If llm-cuda or llm-amd extras exist, update them similarly:
```toml
llm-cuda = [
    "midori-ai-agents-all @ git+https://github.com/Midori-AI-OSS/agents-packages.git#subdirectory=midori-ai-agents-all",
    "torch",
    "torchaudio",
    "torchvision",
    # CUDA-specific packages
]

llm-amd = [
    "midori-ai-agents-all @ git+https://github.com/Midori-AI-OSS/agents-packages.git#subdirectory=midori-ai-agents-all",
    "torch",
    "torchaudio", 
    "torchvision",
    # AMD-specific packages
]
```

## Acceptance Criteria
- [ ] `midori-ai-agents-all` and `midori-ai-logger` added using `uv add`
- [ ] ALL old LLM packages removed from pyproject.toml (breaking change)
- [ ] Essential packages (torch, transformers) retained
- [ ] `uv lock` completes successfully
- [ ] `uv sync --extra llm-cpu` completes successfully
- [ ] All midori-ai packages are installed and importable
- [ ] New framework imports work correctly
- [ ] Build scripts updated if needed
- [ ] GPU/AMD extras updated with logger package
- [ ] No dependency conflicts reported
- [ ] Documentation updated with new dependency info

## Testing Requirements

### Installation Tests
```bash
# Clean install test
cd backend
rm -rf .venv uv.lock
uv sync --extra llm-cpu

# Verify midori packages present
uv pip list | grep midori  # Should show midori packages
```

### Import Tests (Framework Verification)
```bash
# Test NEW framework imports (should succeed)
uv run python -c "from midori_ai_agent_base import get_agent; from midori_ai_logger import get_logger; print('Success')"

# Note: The meta package includes openai and some langchain packages as dependencies,
# so import tests are not the right way to verify breaking changes. The breaking change
# is at the API level (load_llm() vs load_agent()), not package availability.
```

### Build Tests
```bash
# Test builds still work with new dependencies
./build.sh non-llm
./build.sh llm-cpu
```

## Dependencies
- This task must be completed BEFORE all other migration tasks
- Blocks: `32e92203-migrate-llm-loader.md`
- Blocks: `656b2a7e-create-config-support.md`
- Blocks: `c0f04e25-update-chat-room.md`
- Blocks: `96e5fdb9-update-config-routes.md`
- Blocks: `5900934d-update-memory-management.md`

## References
- [Midori AI agents-packages](https://github.com/Midori-AI-OSS/agents-packages)
- [midori-ai-agents-all docs](https://github.com/Midori-AI-OSS/agents-packages/blob/main/midori-ai-agents-all/docs.md)
- Current: `backend/pyproject.toml`
- Build scripts: `build.sh`, `build/`, `packaging/`

## Notes for Coder
- Use `uv add` with git+https URL format for installation
- The `#subdirectory=` part is critical for monorepo structure
- **BREAK backward compatibility** - this is intentional to find issues faster
- Remove ALL old LLM imports and references
- Keep torch and transformers - they're needed by the huggingface backend
- Add midori-ai-logger package for all logging (replace `print` statements)
- The midori-ai-agents-all package is a meta-package that installs all other midori-ai packages
- Consider pinning to a specific version or tag for production (e.g., `@v1.0.0#subdirectory=...`)
- Update `backend/AGENTS.md` has been updated with agent framework information
