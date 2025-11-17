#!/usr/bin/env bash
set -euo pipefail

# Ensure we are in the mounted app directory
cd /app

# Default DB lives under /app/save.db; override via AF_DB_PATH if needed
export PYTHONPATH="/app:${PYTHONPATH:-}"

rm uv.lock

# Optional extras via UV_EXTRA
if [[ -n "${UV_EXTRA:-}" ]]; then
  echo installing with extras
  uv sync --extra "$UV_EXTRA"
  exec uv run app.py --extra "$UV_EXTRA"
else
  echo installing with out extras
  uv sync
  exec uv run app.py
fi



