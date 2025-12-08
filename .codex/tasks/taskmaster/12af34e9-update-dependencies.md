# Update Dependencies for Midori AI Agent Framework

## Task ID
`12af34e9-update-dependencies`

## Priority
High

## Status
READY FOR APPROVAL

## Audit Results (Auditor: 2025-12-08)

### Audit Summary
✅ **PASSED** - All acceptance criteria met. Task is ready for approval and should be moved to `.codex/tasks/taskmaster/`.

### Detailed Findings

#### ✅ Acceptance Criteria Status
- [x] `midori-ai-agents-all` and `midori-ai-logger` added using `uv add`
  - Verified in `backend/pyproject.toml` lines 26-27 and 45-46
  - Git URL format correct with `#subdirectory=` syntax
- [x] ALL old LLM packages removed from pyproject.toml (breaking change)
  - Confirmed: No langchain-*, openai-agents, or langgraph references in pyproject.toml
  - Old packages successfully removed
- [x] Essential packages (torch, transformers) retained
  - Verified: torch, torchaudio, torchvision, transformers, sentence-transformers, accelerate all present
- [x] `uv lock` completes successfully
  - Test result: Resolved 215 packages in 9ms - SUCCESS
- [x] `uv sync --extra llm-cpu` completes successfully
  - Test result: Installed 168 packages successfully
  - All midori-ai packages installed correctly
- [x] All midori-ai packages are installed and importable
  - Verified 15 midori-ai packages installed:
    - midori-ai-agent-base, midori-ai-agent-context-manager, midori-ai-agent-huggingface
    - midori-ai-agent-langchain, midori-ai-agent-openai, midori-ai-agents-all
    - midori-ai-compactor, midori-ai-context-bridge, midori-ai-logger
    - midori-ai-media-lifecycle, midori-ai-media-request, midori-ai-media-vault
    - midori-ai-mood-engine, midori-ai-reranker, midori-ai-vector-manager
- [x] New framework imports work correctly
  - Successfully imported: midori_ai_agent_base (MidoriAiAgentProtocol, get_agent, get_agent_from_config)
  - Successfully imported: midori_ai_agent_openai (OpenAIAgentsAdapter)
  - Successfully imported: midori_ai_agent_huggingface (HuggingFaceLocalAgent)
  - Successfully imported: midori_ai_logger (MidoriAiLogger)
  - Note: Logger import is `MidoriAiLogger` not `get_logger` as shown in example
- [x] Build scripts updated if needed
  - Verified: No hardcoded langchain or openai-agents references in build.sh, build/, packaging/
  - Dockerfiles only contain environment variables (OPENAI_API_URL, OPENAI_API_KEY) which is correct
- [x] GPU/AMD extras updated with logger package
  - Verified in pyproject.toml: llm-cuda and llm-amd both include midori-ai-agents-all and midori-ai-logger
- [x] No dependency conflicts reported
  - `uv lock` ran without conflicts
  - No error or warning messages
- [x] Documentation updated with new dependency info
  - Verified: backend/AGENTS.md updated with agent framework section (lines 32-73)

#### 📝 Notes for Next Tasks
1. **Code Migration NOT Expected**: This is a dependency-only task. Code still uses old langchain/openai imports, which is EXPECTED and CORRECT. Those will be migrated in subsequent tasks:
   - `32e92203-migrate-llm-loader.md` - Will migrate the LLM loader code
   - Other blocked tasks will handle other migrations

2. **Test Import Errors**: Found 13 test collection errors, but ALL are unrelated to dependency changes:
   - `battle_logging` module import errors (battle_logging.handlers, battle_logging.summary)
   - `runs.lifecycle` import errors (REWARD_STAGING_KEYS, RECENT_FOE_COOLDOWN)
   - These are pre-existing issues unrelated to this dependency update

3. **Torch Verification**: Successfully verified torch availability with `llms.torch_checker.is_torch_available()` returning True

4. **Logger API Note**: The midori_ai_logger package exports `MidoriAiLogger` class, not a `get_logger()` function as shown in some examples. Documentation should note this.

#### 🎯 Recommendations
1. **Approve and Move**: Move this task to `.codex/tasks/taskmaster/` immediately
2. **Unblock Migrations**: This unblocks all dependent migration tasks listed in the Dependencies section
3. **Future Documentation**: Consider updating examples to use correct logger import: `from midori_ai_logger import MidoriAiLogger`

### Test Evidence
```bash
# Dependency resolution
$ cd backend && uv lock
Resolved 215 packages in 9ms

# Installation
$ uv sync --extra llm-cpu
Installed 168 packages in 249ms

# Package verification
$ uv pip list | grep midori | wc -l
15

# Torch check
$ uv run python -c "from llms.torch_checker import is_torch_available; print(is_torch_available())"
True

# No conflicts
$ uv lock 2>&1 | grep -i "conflict\|error\|warning"
[No output - clean]
```

### Conclusion
✅ **APPROVED** - All acceptance criteria met. Task completed successfully and ready for migration to taskmaster.

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
