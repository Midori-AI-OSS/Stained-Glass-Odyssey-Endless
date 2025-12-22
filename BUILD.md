# Midori AutoFighter Build System

This document describes how to build Midori AutoFighter locally for development and testing.

**Note:** Midori AI only supports Linux. Windows builds are not supported.

## Build Variants

### Platform
- **Linux** (x64)

### Configurations
- **non-llm**: Base game without LLM support
- **llm-cpu**: Game with CPU-based LLM support
- **llm-cuda**: Game with NVIDIA GPU LLM support (CUDA)
- **llm-amd**: Game with AMD GPU LLM support (ROCm)

## Local Development

### Prerequisites
- [uv](https://github.com/astral-sh/uv) for Python dependency management
- [bun](https://bun.sh/) for JavaScript dependency management
- Python 3.12+

### Manual Build Process

**Important:** The frontend must be built first, as the backend build process requires the compiled frontend files.

1. **Build frontend:**
   ```bash
   cd frontend
   bun install
   bun run build
   cd ..
   ```

2. **Setup backend environment:**
   ```bash
   cd backend
   uv sync
   ```

3. **Install variant dependencies (if needed):**
   ```bash
   # For LLM variants:
   uv sync --extra llm-cpu     # CPU LLM support
   uv sync --extra llm-cuda    # NVIDIA GPU LLM support
   uv sync --extra llm-amd     # AMD GPU LLM support
   ```

4. **Install PyInstaller:**
   ```bash
   uv add --dev pyinstaller
   ```

5. **Build executable:**
   ```bash
   # Linux
   uv run pyinstaller --onefile --add-data ../frontend/build:frontend --clean --name midori-autofighter-non-llm-linux app.py
   ```

### Dependencies by Variant

#### Base Dependencies (all variants)
- quart >= 0.19.0
- quart-cors >= 0.7.0
- websockets >= 12.0

#### LLM Dependencies
- **llm-cpu**: torch, transformers, accelerate
- **llm-cuda**: torch, transformers, accelerate, nvidia-ml-py
- **llm-amd**: torch, transformers, accelerate (with ROCm support)

## Troubleshooting

### Common Issues

1. **Missing Frontend Build**: Ensure you build the frontend **before** building the backend executable. The backend build process requires the compiled frontend files in `frontend/build/`.

2. **Large Build Size**: LLM variants will be significantly larger (1GB+) due to PyTorch and model dependencies.

### Build Optimization

To reduce build size:
- Use `--onefile` flag (already included)
- Consider excluding unused dependencies with `--exclude-module`
- For LLM variants, consider using smaller model variants

## Contributing

When adding new dependencies:
1. Add base dependencies to the main `dependencies` list in `backend/pyproject.toml`
2. Add variant-specific dependencies to appropriate `optional-dependencies` sections
3. Update this README if new build requirements are introduced
4. Test builds locally before pushing