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

### Backend Environment Setup

The backend ships its own `pyproject.toml` in `backend/`. Create and hydrate the
virtual environment with:

```bash
cd backend
uv sync
```

All backend-only commands (linting, targeted tests) should be executed through
`uv run` so they reuse the synced environment, e.g. `uv run pytest backend/tests`.

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

### Running End-to-End Tests

The repository includes Playwright-based end-to-end tests that verify the complete game flow across all variants.

#### Local E2E Testing
```bash
# Install frontend dependencies including Playwright
cd frontend
bun install

# Install Playwright browsers
bunx playwright install --with-deps chromium

# Start the backend in one terminal
cd backend
uv run app.py

# In another terminal, run Playwright tests
cd frontend
bunx playwright test

# View test report
bunx playwright show-report
```

#### E2E Tests in CI

The repository includes two GitHub Actions workflows for E2E testing:
- `.github/workflows/e2e-test-1.yml` - First sub-agent workflow
- `.github/workflows/e2e-test-2.yml` - Second sub-agent workflow

Each workflow tests 3 game variants in parallel (non-llm, llm-cpu, llm-cuda) using a matrix strategy. Each variant is tested as an independent "sub-agent" that:
1. Sets up the environment with appropriate dependencies
2. Builds the frontend
3. Starts the backend server
4. Runs Playwright tests against the running application
5. Uploads test artifacts (reports, videos, screenshots) on failure

To trigger these workflows manually, go to the Actions tab in GitHub and select "Run workflow".

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

### Available Workflows

1. **backend-ci.yml** - Backend linting and unit tests
2. **frontend-ci.yml** - Frontend linting and unit tests  
3. **e2e-test-1.yml** - End-to-end tests with Playwright (sub-agent 1)
4. **e2e-test-2.yml** - End-to-end tests with Playwright (sub-agent 2)
5. **build-all-platforms.yml** - Build executables for all platforms and variants
6. **build-linux.yml** / **build-windows.yml** / **build-android.yml** - Platform-specific builds

The E2E test workflows use a matrix strategy to test 3 game variants (non-llm, llm-cpu, llm-cuda) in parallel, with each variant running as an independent job.

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