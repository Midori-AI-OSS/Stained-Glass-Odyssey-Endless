# Midori AutoFighter Build System

This document describes how to build the Midori AutoFighter game locally for supported platforms.

## Build Variants

### Platforms
- **Linux** (x64)
- **macOS** (x64/ARM64)

### Configurations
- **non-llm**: Base game without LLM support
- **llm-cpu**: Game with CPU-based LLM support
- **llm-cuda**: Game with NVIDIA GPU LLM support (CUDA)
- **llm-amd**: Game with AMD GPU LLM support (ROCm)

## Local Development

### Prerequisites
- [uv](https://github.com/astral-sh/uv) for Python dependency management
- Python 3.12+

### Quick Build
Use the provided build script:

```bash
# Build non-llm variant for current platform
./build.sh

# Build specific variant
./build.sh llm-cpu

# Build for specific platform
./build.sh non-llm linux
```

### Manual Build Process

1. **Setup environment:**
   ```bash
   cd legacy
   uv sync
   ```

2. **Install variant dependencies (if needed):**
   ```bash
   # For LLM variants:
   uv sync --extra llm-cpu     # CPU LLM support
   uv sync --extra llm-cuda    # NVIDIA GPU LLM support
   uv sync --extra llm-amd     # AMD GPU LLM support
   ```

3. **Install PyInstaller:**
   ```bash
   uv add --dev pyinstaller
   ```

4. **Create asset directories:**
   ```bash
   mkdir -p photos music
   ```

5. **Build executable:**
   ```bash
   # Linux/macOS
   uv run pyinstaller --onefile --add-data photos:photos --add-data music:music --clean --name midori-autofighter main.py
   ```

### Dependencies by Variant

#### Base Dependencies (all variants)
- colorama >= 0.4.6
- halo >= 0.0.31
- pygame >= 2.6.1
- snakeviz >= 2.2.2

#### LLM Dependencies
- **llm-cpu**: torch, transformers, accelerate
- **llm-cuda**: torch, transformers, accelerate, nvidia-ml-py
- **llm-amd**: torch, transformers, accelerate (with ROCm support)

## Troubleshooting

### Common Issues

1. **Missing Assets**: If photos/music directories don't exist, they're created automatically as empty directories.

2. **Large Build Size**: LLM variants will be significantly larger (100MB+) due to PyTorch and model dependencies.

### Build Optimization

To reduce build size:
- Use `--onefile` flag (already included)
- Consider excluding unused dependencies with `--exclude-module`
- For LLM variants, consider using smaller model variants

## Contributing

When adding new dependencies:
1. Add base dependencies to the main `dependencies` list in `pyproject.toml`
2. Add variant-specific dependencies to appropriate `optional-dependencies` sections
3. Update this README if new build requirements are introduced
4. Test builds locally before pushing

## Architecture

```
backend/                    # Backend game logic
├── app.py                  # Application entry point
├── pyproject.toml          # Dependencies and build config
└── [game source files]

frontend/                   # Frontend UI
├── src/                    # Svelte components
└── package.json            # Node dependencies

build.sh                    # Local build helper script
```