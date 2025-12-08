# Agent Configuration

AutoFighter uses the Midori AI Agent Framework's config file system for centralized LLM/LRM configuration.

## Overview

The agent framework provides a flexible configuration system that supports multiple backends, environment variable substitution, and backend-specific overrides. This eliminates the need for multiple environment variables and provides a single source of truth for agent configuration.

## Config File Location

The config file `config.toml` should be placed in the `backend/` directory:

```
backend/
├── config.toml          # Your actual config (not committed)
├── config.toml.example  # Template with documentation (committed)
└── scripts/
    └── validate_config.py  # Validation tool
```

## Config Format

The configuration uses TOML format with a hierarchical structure:

### Base Configuration

```toml
[midori_ai_agent_base]
backend = "openai"              # Backend selection
model = "gpt-5"          # Model name
api_key = "${OPENAI_API_KEY}"  # API key (with env var substitution)
base_url = "${OPENAI_API_URL}" # Base URL (with env var substitution)
```

### Reasoning Configuration (Optional)

```toml
[midori_ai_agent_base.reasoning_effort]
effort = "low"                # Reasoning depth
```

### Backend-Specific Overrides

```toml
[midori_ai_agent_base.openai]
# OpenAI-specific settings override base when using openai backend
temperature = 0.7
max_tokens = 2048

[midori_ai_agent_base.huggingface]
# HuggingFace-specific settings override base when using huggingface backend
model = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
device = "auto"
torch_dtype = "auto"
load_in_8bit = false

[midori_ai_agent_base.langchain]
# Langchain-specific settings override base when using langchain backend
# Configuration depends on specific provider
```

## Environment Variable Substitution

The config supports environment variable substitution using `${VAR_NAME}` syntax:

- `api_key = "${OPENAI_API_KEY}"` - Reads from OPENAI_API_KEY environment variable
- `base_url = "${OPENAI_API_URL}"` - Reads from OPENAI_API_URL environment variable

This allows you to:
1. Keep secrets out of the config file
2. Use different values in different environments
3. Version control the config.toml.example without exposing secrets

## Backend Selection

Three backends are supported:

### 1. OpenAI Backend (`backend = "openai"`)
For OpenAI API, Ollama, LocalAI, and compatible services.

**Use cases:**
- Production deployments with OpenAI API
- Local development with Ollama
- Custom LLM servers with OpenAI-compatible API

**Configuration example:**
```toml
[midori_ai_agent_base]
backend = "openai"
model = "gpt-5"
api_key = "${OPENAI_API_KEY}"
base_url = "http://192.168.1.100:11434/v1"
```

### 2. HuggingFace Backend (`backend = "huggingface"`)
For local inference with HuggingFace models.

**Use cases:**
- Local development without external API
- Privacy-sensitive deployments
- Offline usage

**Configuration example:**
```toml
[midori_ai_agent_base]
backend = "huggingface"
model = "openai/gpt-oss-20b"

[midori_ai_agent_base.huggingface]
device = "cuda"
torch_dtype = "float16"
load_in_8bit = true
```

### 3. Langchain Backend (`backend = "langchain"`)
For Langchain-based providers.

**Use cases:**
- Integration with Langchain ecosystem
- Custom Langchain providers

**Configuration example:**
```toml
[midori_ai_agent_base]
backend = "langchain"
model = "openai/gpt-5"
```

## Configuration Priority

Settings are resolved in this order (highest to lowest priority):

1. **Function arguments** - Passed directly to `load_agent()`
2. **Backend-specific config section** - E.g., `[midori_ai_agent_base.openai]`
3. **Base config section** - E.g., `[midori_ai_agent_base]`
4. **Environment variables** - E.g., `OPENAI_API_URL`, `AF_LLM_MODEL`
5. **Built-in defaults** - Framework defaults

This allows you to:
- Set general defaults in base config
- Override per backend
- Override at runtime via function arguments
- Fall back to environment variables if config doesn't exist

## Validation

Use the validation script to check your configuration:

```bash
cd backend
uv run python scripts/validate_config.py
```

The script will:
- Check if the config file exists
- Validate the TOML syntax
- Check for required fields
- Verify environment variable substitution
- Display the loaded configuration

## Security Best Practices

1. **Never commit config.toml** - It may contain secrets
   - The .gitignore excludes it automatically
   - Only commit config.toml.example

2. **Use environment variables for secrets**
   - API keys: `api_key = "${OPENAI_API_KEY}"`
   - URLs may be in config if not sensitive

3. **Set restrictive file permissions**
   ```bash
   chmod 600 backend/config.toml
   ```

## Common Configurations

### Remote LRM Server (Using Your Computer's IP)
```toml
[midori_ai_agent_base]
backend = "openai"
model = "gpt-oss:20b"
api_key = "not-needed"
base_url = "http://192.168.1.100:11434/v1"
```

### Midori AI Proxy
```toml
[midori_ai_agent_base]
backend = "openai"
model = "gpt-oss:20b"
api_key = "${OPENAI_API_KEY}"
base_url = "https://ai-proxy.midori-ai.xyz"
```

### Local Inference (CPU)
```toml
[midori_ai_agent_base]
backend = "huggingface"
model = "openai/gpt-oss-20b"

[midori_ai_agent_base.huggingface]
device = "cpu"
torch_dtype = "float32"
```

### Local Inference (GPU with Quantization)
```toml
[midori_ai_agent_base]
backend = "huggingface"
model = "openai/gpt-oss-20b"

[midori_ai_agent_base.huggingface]
device = "cuda"
torch_dtype = "float16"
load_in_8bit = true
max_new_tokens = 512
temperature = 0.7
```

## Troubleshooting

### Config file not found
```bash
cd backend
cp config.toml.example config.toml
# Edit config.toml with your settings
```

### Environment variables not substituted
Make sure environment variables are set before loading config:
```bash
export OPENAI_API_KEY="your-key-here"
export OPENAI_API_URL="http://localhost:11434/v1"
```

### Validation fails
Run validation with debug output:
```bash
cd backend
uv run python scripts/validate_config.py
```

### Backend not available
Install the required dependencies:
```bash
cd backend
# For CPU inference
uv sync --extra llm-cpu

# For CUDA inference
uv sync --extra llm-cuda

# For AMD inference
uv sync --extra llm-amd
```

## Future Enhancements

Planned improvements for the config system:

1. **Config hot-reloading** - Reload config without restarting
2. **Multiple profiles** - Switch between dev/prod configs
3. **Config validation in CI** - Ensure example is always valid
4. **Web UI for config** - Edit config through the frontend
5. **Config templates** - Pre-built configs for common setups

## References

- Template file: `backend/config.toml.example`
- Validation script: `backend/scripts/validate_config.py`
- Agent framework docs: https://github.com/Midori-AI-OSS/agents-packages
- Backend README: `backend/README.md`

## Related Documentation

- [Agent Framework Migration](./agent-framework.md) (future)
- [LLM Loader Implementation](../backend/llms/agent_loader.py) (future)
- [Backend README](../../backend/README.md)

## Runtime Configuration API

In addition to the config file, AutoFighter provides REST API endpoints for runtime configuration management. These endpoints allow the frontend to discover and modify LRM settings without restarting the server.

### Endpoints

#### GET /config/lrm
Returns current LRM configuration and available options.

**Response:**
```json
{
  "current_model": "openai/gpt-oss-20b",
  "current_backend": "auto",
  "available_backends": ["auto", "openai", "huggingface"],
  "available_models": ["openai/gpt-oss-20b", "openai/gpt-oss-120b", "gguf", "remote-openai"]
}
```

#### POST /config/lrm
Update model and/or backend configuration.

**Request:**
```json
{
  "model": "openai/gpt-oss-120b",  // optional
  "backend": "openai"                // optional (auto, openai, or huggingface)
}
```

**Response:**
```json
{
  "current_model": "openai/gpt-oss-120b",
  "current_backend": "openai"
}
```

#### POST /config/lrm/backend
Update backend only (convenience endpoint).

**Request:**
```json
{
  "backend": "huggingface"  // required: auto, openai, or huggingface
}
```

**Response:**
```json
{
  "current_backend": "huggingface"
}
```

#### POST /config/lrm/test
Test the current LRM configuration with an optional custom prompt.

**Request:**
```json
{
  "prompt": "Hello, how are you?"  // optional
}
```

**Response:**
```json
{
  "response": "I'm doing well, thank you!",
  "backend": "agent"  // or "legacy" if agent framework not available
}
```

### Backend Selection

The `backend` parameter controls which agent framework backend is used:

- **`auto`** (default): Automatically selects backend based on environment
  - Uses OpenAI backend if `OPENAI_API_URL` is set
  - Falls back to HuggingFace backend if torch is available
  - This is the recommended setting for most use cases

- **`openai`**: Forces use of OpenAI-compatible backend
  - Used for OpenAI API, Ollama, LocalAI, etc.
  - Requires `OPENAI_API_URL` environment variable

- **`huggingface`**: Forces use of HuggingFace local inference
  - Requires torch and transformers libraries
  - Runs model locally on CPU or GPU

### Storage

Runtime configuration changes are persisted to the database in the `options` table:
- `lrm_backend`: Stores the backend selection
- `lrm_model`: Stores the model name

These settings take precedence over config file and environment variables when the agent is loaded.

### Implementation

Configuration endpoints are implemented in `backend/routes/config.py` using the options system defined in `backend/options.py`. The endpoints support both the legacy LLM loader and the new agent framework, with automatic fallback for backward compatibility.
