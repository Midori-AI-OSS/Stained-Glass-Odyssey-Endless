# Create Config File Support for Agent Framework

## Task ID
`656b2a7e-create-config-support`

## Priority
High

## Status
WIP

## Description
Add support for the Midori AI Agent Framework's config file system (`config.toml`). This allows users to configure agent backends, models, and API settings without editing code or setting many environment variables.

## Context
Currently, LRM configuration is done via:
- Environment variables (`OPENAI_API_URL`, `OPENAI_API_KEY`, `AF_LLM_MODEL`)
- Options database (`options` table)
- Hardcoded defaults in code

The Agent Framework provides a `config.toml` file system that:
- Centralizes configuration
- Supports multiple backends
- Allows backend-specific overrides
- Works with `get_agent_from_config()` factory

## Rationale
- **User-Friendly**: Single config file instead of many env vars
- **Self-Documenting**: Comments in config explain each option
- **Flexible**: Easy to switch between backends/models
- **Portable**: Config file can be version controlled (minus secrets)
- **Framework-Native**: Uses framework's built-in config system

## Objectives
1. Create `backend/config.toml` template with examples
2. Update agent loader to support config file
3. Provide fallback to environment variables
4. Document config options
5. Add config validation
6. Support secrets management

## Implementation Steps

### Step 1: Create Config Template
Create `backend/config.toml`:

```toml
# Midori AI AutoFighter - Agent Configuration
# Copy this file to config.toml and customize for your setup
# DO NOT commit config.toml with real API keys!

[midori_ai_agent_base]
# Backend selection: "openai", "huggingface", or "langchain"
backend = "openai"

# Model name (backend-specific)
# OpenAI: "gpt-4", "carly-agi-pro", etc.
# HuggingFace: "TinyLlama/TinyLlama-1.1B-Chat-v1.0", "meta-llama/Llama-2-7b-chat-hf"
# Langchain: depends on provider
model = "gpt-oss:20b"

# API key (use environment variable for security: ${OPENAI_API_KEY})
# For Ollama and similar, leave empty or set to "not-needed"
api_key = "${OPENAI_API_KEY}"

# Base URL for API (optional)
# Examples:
#   OpenAI: "https://api.openai.com/v1"
#   Ollama: "http://localhost:11434/v1"
#   Custom: "https://your-llm-server.com/v1"
base_url = "${OPENAI_API_URL}"

# Optional: Reasoning effort configuration
[midori_ai_agent_base.reasoning_effort]
effort = "high"              # Options: "none", "minimal", "low", "medium", "high"
generate_summary = "detailed" # Options: "auto", "concise", "detailed"
summary = "detailed"         # Options: "auto", "concise", "detailed"

# Backend-specific overrides (optional)
# Settings here override base settings when that backend is used

[midori_ai_agent_base.openai]
# OpenAI-specific overrides
# model = "gpt-4-turbo"      # Use different model for OpenAI backend

[midori_ai_agent_base.huggingface]
# HuggingFace-specific settings
model = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
device = "auto"               # Options: "auto", "cpu", "cuda", "mps"
torch_dtype = "auto"          # Options: "auto", "float16", "float32", "bfloat16"
max_new_tokens = 512
temperature = 0.7
load_in_8bit = false          # Enable 8-bit quantization
load_in_4bit = false          # Enable 4-bit quantization

[midori_ai_agent_base.langchain]
# Langchain-specific settings
# model = "llama3:8b"
```

### Step 2: Update Agent Loader for Config Support
Modify `backend/llms/agent_loader.py`:

```python
"""Agent loader with config file support."""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING

from midori_ai_agent_base import (
    MidoriAiAgentProtocol,
    get_agent,
    get_agent_from_config,
    load_agent_config,
)

if TYPE_CHECKING:
    from midori_ai_agent_base import AgentConfig

from .torch_checker import is_torch_available

log = logging.getLogger(__name__)


def find_config_file() -> Path | None:
    """Find config.toml in backend directory or parent directories.
    
    Returns:
        Path to config.toml if found, None otherwise
    """
    # Start from backend directory
    current = Path(__file__).parent.parent
    
    # Search upward for config.toml
    for _ in range(5):  # Max 5 levels up
        config_path = current / "config.toml"
        if config_path.exists():
            return config_path
        current = current.parent
    
    return None


async def load_agent(
    backend: str | None = None,
    model: str | None = None,
    validate: bool = True,
    use_config: bool = True,
) -> MidoriAiAgentProtocol:
    """Load an agent using the Midori AI Agent Framework.
    
    Args:
        backend: Backend type ("openai", "huggingface", "langchain")
                 If None, auto-selects based on config or environment
        model: Model name to use
               If None, uses config or environment variable
        validate: Whether to validate the agent
        use_config: Whether to try loading from config.toml
    
    Returns:
        Agent implementing MidoriAiAgentProtocol
    """
    # Try loading from config file first
    if use_config:
        config_path = find_config_file()
        if config_path:
            log.info(f"Loading agent from config: {config_path}")
            try:
                agent = await get_agent_from_config(
                    config_path=str(config_path),
                    backend=backend,  # Allow override
                    model=model,      # Allow override
                )
                if validate:
                    log.info(f"Agent loaded from config: {config_path}")
                return agent
            except Exception as e:
                log.warning(f"Failed to load from config: {e}, falling back to env vars")
    
    # Fall back to environment variables
    log.info("Loading agent from environment variables")
    
    # Auto-detect backend based on environment
    if backend is None:
        openai_url = os.getenv("OPENAI_API_URL", "unset")
        if openai_url != "unset":
            backend = "openai"
        elif is_torch_available():
            backend = "huggingface"
        else:
            backend = "langchain"
    
    # Get model from environment if not specified
    if model is None:
        model = os.getenv("AF_LLM_MODEL", "gpt-oss:20b")
    
    # Get API configuration
    api_key = os.getenv("OPENAI_API_KEY", "")
    base_url = os.getenv("OPENAI_API_URL")
    
    # Create agent using framework factory
    agent = await get_agent(
        backend=backend,
        model=model,
        api_key=api_key,
        base_url=base_url,
    )
    
    if validate:
        log.info(f"Agent loaded: backend={backend}, model={model}")
    
    return agent


def get_agent_config() -> AgentConfig | None:
    """Get current agent configuration from file.
    
    Returns:
        AgentConfig if config file exists, None otherwise
    """
    config_path = find_config_file()
    if config_path:
        try:
            return load_agent_config(config_path=str(config_path))
        except Exception as e:
            log.error(f"Failed to load config: {e}")
            return None
    return None


__all__ = ["load_agent", "get_agent_config", "find_config_file"]
```

### Step 3: Add Config to .gitignore
Update `.gitignore`:

```gitignore
# Agent configuration (may contain secrets)
config.toml
backend/config.toml

# But keep the example
!config.toml.example
!backend/config.toml.example
```

### Step 4: Create Config Validation Script
Create `backend/scripts/validate_config.py`:

```python
"""Validate config.toml file."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from midori_ai_agent_base import load_agent_config


def validate_config(config_path: str = "config.toml") -> bool:
    """Validate a config file.
    
    Args:
        config_path: Path to config file
    
    Returns:
        True if valid, False otherwise
    """
    try:
        config = load_agent_config(config_path=config_path)
        
        print(f"✓ Config file is valid: {config_path}")
        print(f"  Backend: {config.backend}")
        print(f"  Model: {config.model}")
        print(f"  Base URL: {config.base_url or '(not set)'}")
        
        if config.reasoning_effort:
            print(f"  Reasoning Effort: {config.reasoning_effort.effort}")
        
        if config.extra:
            print(f"  Extra settings: {list(config.extra.keys())}")
        
        return True
    except FileNotFoundError:
        print(f"✗ Config file not found: {config_path}")
        return False
    except Exception as e:
        print(f"✗ Config validation failed: {e}")
        return False


if __name__ == "__main__":
    import sys
    
    config_path = sys.argv[1] if len(sys.argv) > 1 else "config.toml"
    success = validate_config(config_path)
    sys.exit(0 if success else 1)
```

### Step 5: Add Config Setup to README
Update `backend/README.md`:

```markdown
## Configuration

AutoFighter supports two configuration methods:

### Option 1: Config File (Recommended)

1. Copy the example config:
   ```bash
   cp config.toml.example config.toml
   ```

2. Edit `config.toml` with your settings:
   ```toml
   [midori_ai_agent_base]
   backend = "openai"
   model = "gpt-oss:20b"
   api_key = "${OPENAI_API_KEY}"
   base_url = "${OPENAI_API_URL}"
   ```

3. Set any referenced environment variables:
   ```bash
   export OPENAI_API_URL="http://localhost:11434/v1"
   export OPENAI_API_KEY="not-needed"
   ```

4. Validate your config:
   ```bash
   uv run python scripts/validate_config.py
   ```

### Option 2: Environment Variables

Set these environment variables:
- `OPENAI_API_URL` - Base URL for API
- `OPENAI_API_KEY` - API key (or empty for Ollama)
- `AF_LLM_MODEL` - Model name

Example:
```bash
export OPENAI_API_URL="http://localhost:11434/v1"
export OPENAI_API_KEY="not-needed"
export AF_LLM_MODEL="llama3:8b"
```

### Configuration Priority

Settings are resolved in this order (highest to lowest priority):
1. Function arguments in code
2. Config file backend-specific section
3. Config file base section
4. Environment variables
5. Built-in defaults
```

### Step 6: Test Config Loading
Create test script `backend/test_config.py`:

```python
"""Test config file loading."""
import asyncio

from llms.agent_loader import find_config_file, get_agent_config, load_agent


async def test_config():
    """Test configuration loading."""
    # Test finding config file
    config_path = find_config_file()
    print(f"Config path: {config_path}")
    
    # Test loading config
    config = get_agent_config()
    if config:
        print(f"Backend: {config.backend}")
        print(f"Model: {config.model}")
    else:
        print("No config file found, will use env vars")
    
    # Test loading agent with config
    print("\nLoading agent...")
    agent = await load_agent(use_config=True)
    print(f"Agent loaded: {agent}")
    
    # Test that env vars still work
    print("\nLoading agent without config...")
    agent2 = await load_agent(use_config=False)
    print(f"Agent loaded: {agent2}")


if __name__ == "__main__":
    asyncio.run(test_config())
```

Run test:
```bash
cd backend
uv run python test_config.py
```

### Step 7: Document Config in .codex
Create `.codex/implementation/agent-config.md`:

```markdown
# Agent Configuration

AutoFighter uses the Midori AI Agent Framework's config file system.

## Config File Location

The config file `config.toml` should be placed in the `backend/` directory.

## Config Format

See `backend/config.toml.example` for a complete example.

## Environment Variable Substitution

The config supports environment variable substitution using `${VAR_NAME}` syntax:
- `api_key = "${OPENAI_API_KEY}"` - Reads from environment
- `base_url = "${OPENAI_API_URL}"` - Reads from environment

## Backend Selection

Three backends are supported:
1. `openai` - OpenAI Agents SDK (for OpenAI API, Ollama, etc.)
2. `huggingface` - Local inference with HuggingFace models
3. `langchain` - Langchain backend

## Config Priority

1. Function arguments (highest)
2. Backend-specific config section
3. Base config section
4. Environment variables
5. Built-in defaults (lowest)
```

## Acceptance Criteria
- [ ] `config.toml.example` created with documentation
- [ ] `agent_loader.py` updated to support config files
- [ ] Config file loading tested and working
- [ ] Environment variable fallback still works
- [ ] `.gitignore` updated to exclude `config.toml`
- [ ] Validation script created and working
- [ ] README.md updated with config documentation
- [ ] `.codex/implementation/agent-config.md` created
- [ ] Config file can reference environment variables
- [ ] Backend-specific overrides work
- [ ] All three backends can be configured
- [ ] Linting passes

## Testing Requirements

### Manual Tests
```bash
# Test with config file
cd backend
cp config.toml.example config.toml
# Edit config.toml
uv run python test_config.py

# Test validation
uv run python scripts/validate_config.py

# Test without config file (env vars only)
mv config.toml config.toml.bak
uv run python test_config.py
mv config.toml.bak config.toml
```

### Unit Tests
```python
# In tests/test_config.py
import pytest
from llms.agent_loader import find_config_file, get_agent_config


def test_find_config():
    """Test finding config file."""
    path = find_config_file()
    assert path is None or path.exists()


def test_get_config():
    """Test loading config."""
    config = get_agent_config()
    # May be None if config file doesn't exist
    if config:
        assert config.backend in ["openai", "huggingface", "langchain"]
```

## Dependencies
- Requires: `12af34e9-update-dependencies.md` (agent framework installed)
- Can be done in parallel with: `32e92203-migrate-llm-loader.md`
- Helps: All other tasks (provides better configuration)

## References
- [midori-ai-agent-base config docs](https://github.com/Midori-AI-OSS/agents-packages/blob/main/midori-ai-agent-base/docs.md#configuration-file)
- New files: `backend/config.toml.example`, `backend/scripts/validate_config.py`
- Updated: `backend/llms/agent_loader.py`, `backend/README.md`, `.gitignore`

## Notes for Coder
- Config file is optional - env vars should still work
- Use `${VAR_NAME}` syntax for environment variable substitution
- Don't commit real API keys in config files
- The framework searches upward for config.toml
- Backend-specific sections override base settings
- Config validation helps users debug configuration issues
- Document all config options with comments in .example file
