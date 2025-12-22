# Agent Configuration

AutoFighter uses the Midori AI Agent Framework's config file system.

## Config File Location

The config file `config.toml` should be placed in the `backend/` directory.

## Config Format

See `backend/config.toml` for a complete example.

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
