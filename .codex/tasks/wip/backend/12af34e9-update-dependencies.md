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

## Objectives
1. Add `midori-ai-agents-all` package to dependencies
2. Remove redundant individual packages
3. Keep essential packages (torch, transformers) that are still needed
4. Maintain all existing LLM functionality
5. Ensure all optional dependency groups still work

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

### Step 2: Update pyproject.toml

Modify `backend/pyproject.toml`:

```toml
[project.optional-dependencies]
llm-cpu = [
    # Core LLM framework
    "midori-ai-agents-all @ git+https://github.com/Midori-AI-OSS/agents-packages.git#subdirectory=midori-ai-agents-all",
    
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

Remove these (now provided by midori-ai-agents-all):
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

### Step 5: Test Imports
Create a test script to verify imports work:
```python
# Test framework imports
from midori_ai_agent_base import MidoriAiAgentProtocol, AgentPayload, AgentResponse
from midori_ai_agent_base import get_agent, get_agent_from_config
from midori_ai_agent_openai import OpenAIAgentsAdapter
from midori_ai_agent_huggingface import HuggingFaceLocalAgent
from midori_ai_agent_langchain import LangChainAdapter

# Test that old imports still work (for backward compatibility testing)
import openai
from openai import AsyncOpenAI
import langchain_core
import transformers

print("All imports successful!")
```

Run test:
```bash
cd backend
uv run python test_imports.py
```

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
- [ ] `midori-ai-agents-all` added to pyproject.toml
- [ ] Redundant packages removed from pyproject.toml
- [ ] Essential packages (torch, transformers) retained
- [ ] `uv lock` completes successfully
- [ ] `uv sync --extra llm-cpu` completes successfully
- [ ] All midori-ai packages are installed and importable
- [ ] Old package imports still work (for transition period)
- [ ] Build scripts updated if needed
- [ ] GPU/AMD extras updated if they exist
- [ ] No dependency conflicts reported
- [ ] Documentation updated with new dependency info

## Testing Requirements

### Installation Tests
```bash
# Clean install test
cd backend
rm -rf .venv uv.lock
uv sync --extra llm-cpu

# Verify all packages present
uv pip list | grep -E "midori|langchain|openai|torch|transformers"
```

### Import Tests
```bash
# Test framework imports
uv run python -c "from midori_ai_agent_base import get_agent; print('Success')"

# Test old imports still work
uv run python -c "import openai, langchain_core; print('Success')"
```

### Build Tests
```bash
# Test non-LLM build still works
./build.sh non-llm

# Test LLM build still works (if time permits)
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
- Use git+https URL format for direct installation from GitHub
- The `#subdirectory=` part is critical for monorepo structure
- Keep torch and transformers - they're needed by the huggingface backend
- The midori-ai-agents-all package is a meta-package that installs all other midori-ai packages
- You can verify the meta-package contents by checking its pyproject.toml in the cloned agents-packages repo
- Consider pinning to a specific version or tag for production (e.g., `@v1.0.0#subdirectory=...`)
- The framework recommends v1 for version locking, but allows using main branch for latest features
