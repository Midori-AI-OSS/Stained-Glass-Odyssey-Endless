# Development Guide

This document explains how to set up and work with the Midori AutoFighter development environment.

## Tool Requirements

### Option 1: Modern Tools (Recommended)
- **Python**: Install [uv](https://github.com/astral-sh/uv) for fast Python package management
- **Node.js**: Install [bun](https://bun.sh/) for fast JavaScript package management

### Option 2: Standard Tools (Fallback)
- **Python**: Standard `python3` and `pip3` (comes with most systems)
- **Node.js**: Standard `npm` and `node` (install from [nodejs.org](https://nodejs.org/))

## Quick Start

### Running Tests
```bash
./run-tests.sh
```

The script will automatically detect available tools and use the best option:
- With `uv` and `bun`: Fast, modern tooling (same as CI)
- Without `uv`/`bun`: Falls back to `python3`/`pip3` and `npm`

### Character Plugin Boundaries
- Read the plugin boundary reminder in
  [`.codex/instructions/plugin-system.md`](.codex/instructions/plugin-system.md)
  before touching combat helpers. All spawn weighting, boss behaviours, and
  passive effects must live in the relevant plugin modules so shared battle
  utilities remain character-agnostic.

### Building the Application
```bash
./build.sh [variant] [platform]
```

Example:
```bash
./build.sh non-llm linux
./build.sh llm-cpu windows
```

## Tool Detection Behavior

### Backend (Python)
- **With `uv`**: Uses `uv venv && uv sync` for fast dependency management
- **Without `uv`**: Uses `python3 -m venv venv && pip3 install -e .` for compatibility

### Frontend (Node.js)
- **With `bun`**: Uses `bun install && bun run build/test` for fast JavaScript tooling
- **Without `bun`**: Uses `npm install && npm run build` for standard Node.js workflow
- **Frontend tests**: Require `bun` (uses `bun:test` API), skip gracefully if unavailable

## CI Workflow

The GitHub Actions CI workflow uses modern tools:
- Backend: `setup-uv@v3` action installs `uv`
- Frontend: `setup-bun@v1` action installs `bun`

Local development scripts automatically adapt to available tools, ensuring compatibility across different environments.

## Troubleshooting

### "command not found: uv"
This is normal if you haven't installed `uv`. The scripts will fall back to standard Python tools.

### "command not found: bun"
This is normal if you haven't installed `bun`. The scripts will fall back to `npm` for builds and skip tests (which require `bun:test` API).

### Virtual Environment Issues
If you encounter Python virtual environment issues, try:
```bash
rm -rf backend/venv
./run-tests.sh
```

The script will recreate the environment automatically.

## Installation Guide

### Installing Modern Tools

#### Install uv (Python)
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### Install bun (Node.js)
```bash
curl -fsSL https://bun.sh/install | bash
```

### Installing Standard Tools

#### Python (if not already installed)
- Ubuntu/Debian: `sudo apt install python3 python3-pip python3-venv`
- macOS: `brew install python3`
- Windows: Download from [python.org](https://python.org)

#### Node.js (if not already installed)
- All platforms: Download from [nodejs.org](https://nodejs.org)
- Ubuntu/Debian: `sudo apt install nodejs npm`
- macOS: `brew install node`