# Midori AI AutoFighter

A web-based auto-battler game featuring strategic party management, elemental combat, and character progression.

## Daily Login Rewards

Log in each day, clear at least three rooms, and claim a streak-based bundle of
damage-type upgrade items. Rewards reset at 2:00 AM Pacific Time and scale up
every seven and one hundred consecutive days.

## Quick Start with Docker Compose (Recommended)

The easiest way to run Midori AI AutoFighter is with Docker Compose. Choose one of the four variants below:

### Prerequisites

- Install [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)

### Option 1: Standard Version (Recommended for most users)

```bash
docker compose up --build frontend backend
```

**Access the game:** Open your web browser and go to `http://YOUR_SYSTEM_IP:59001`

### Option 2: LLM-Enhanced Version with NVIDIA GPU Support

For users with NVIDIA graphics cards who want LLM-powered chat features:

> **⚠️ Note:** If you have already started the standard version, run `docker compose down` first to stop the existing backend.

```bash
docker compose --profile llm-cuda up --build
```

**Access the game:** Open your web browser and go to `http://YOUR_SYSTEM_IP:59001`

### Option 3: LLM-Enhanced Version with AMD GPU Support

For users with AMD graphics cards who want LLM-powered chat features:

> **⚠️ Note:** If you have already started the standard version, run `docker compose down` first to stop the existing backend.

```bash
docker compose --profile llm-amd up --build
```

**Access the game:** Open your web browser and go to `http://YOUR_SYSTEM_IP:59001`

### Option 4: LLM-Enhanced Version with CPU-Only Support

For users who want LLM-powered chat features but don't have a compatible GPU:

> **⚠️ Note:** If you have already started the standard version, run `docker compose down` first to stop the existing backend.

```bash
docker compose --profile llm-cpu up --build
```

**Access the game:** Open your web browser and go to `http://YOUR_SYSTEM_IP:59001`

## Alternative Installation: Development Setup

> **⚠️ Note:** This installation method is primarily intended for developers. For most users, we recommend using Docker Compose above.

If you prefer to run the game without Docker or want to modify the code:

### Prerequisites

Install the required tools:

```bash
# Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

```bash
# Install bun (JavaScript package manager)
curl -fsSL https://bun.sh/install | bash
```

### Setup Steps

1. **Start the Backend** (in one terminal):
   ```bash
   cd backend
   uv venv
   uv run app.py
   ```
   
   **For LLM support:** Install additional dependencies with `uv sync --extra llm-cpu`, `uv sync --extra llm-cuda`, or `uv sync --extra llm-amd` before running the backend.

2. **Start the Frontend** (in another terminal):
   ```bash
   cd frontend
   bun install
   bun run dev
   ```

**Access the game:** Open your web browser and go to `http://YOUR_SYSTEM_IP:59001`

## Getting Help

- **Game Information:** See [ABOUTGAME.md](ABOUTGAME.md) for detailed game mechanics, features, and character information
- **Development:** See [DEVELOPMENT.md](DEVELOPMENT.md) for development environment setup
- **Building:** See [BUILD.md](BUILD.md) for building standalone executables
- **Issues:** Report bugs or request features on [GitHub Issues](../../issues)

## Troubleshooting

**Docker Compose fails with DNS/network errors:** This is a known issue in some environments. Use the alternative UV & Bun installation method instead.

**Services won't start:** Make sure ports 59001 and 59002 are not being used by other applications.

## Download Prebuilt Versions

You can also download prebuilt executables from our [Releases page](../../releases) instead of running from source.
