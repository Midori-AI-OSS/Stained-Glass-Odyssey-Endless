#!/bin/bash

# Build script for Midori AutoFighter
# Usage: ./build.sh [variant] [platform]
# Variants: non-llm, llm-cpu, llm-cuda, llm-amd
# Platforms: linux, darwin (macOS) - auto-detected if not specified

set -e

VARIANT=${1:-non-llm}
PLATFORM=${2:-$(uname -s | tr '[:upper:]' '[:lower:]')}

echo "Building Midori AutoFighter - Variant: $VARIANT, Platform: $PLATFORM"

# Desktop builds (Linux/macOS) - build backend + frontend
echo "Building desktop application..."

# Build frontend first
echo "Building frontend..."
cd frontend

# Detect available Node tools
if command -v bun >/dev/null 2>&1; then
  echo "Using bun for Node.js environment"
  bun install
  bun run build
else
  echo "bun not found, using npm"
  npm install
  npm run build
fi

cd ..

# Build backend
echo "Setting up backend build environment..."
cd backend

# Setup environment with tool detection
if command -v uv >/dev/null 2>&1; then
  echo "Using uv for Python environment"
  echo "Installing backend dependencies..."
  uv sync
  
  # Install variant-specific dependencies
  case "$VARIANT" in
      "llm-cpu")
          echo "Installing CPU LLM dependencies..."
          uv sync --extra llm-cpu
          ;;
      "llm-cuda")
          echo "Installing CUDA LLM dependencies..."
          uv sync --extra llm-cuda
          ;;
      "llm-amd")
          echo "Installing AMD LLM dependencies..."
          uv sync --extra llm-amd
          ;;
      "non-llm")
          echo "Using base dependencies (no LLM)..."
          ;;
      *)
          echo "Unknown variant: $VARIANT"
          echo "Available variants: non-llm, llm-cpu, llm-cuda, llm-amd"
          exit 1
          ;;
  esac
  
  # Install PyInstaller
  echo "Installing PyInstaller..."
  uv add --dev pyinstaller
  
  # Build executable
  echo "Building executable..."
  PYTHON_RUN="uv run"
else
  echo "uv not found, using standard Python tools"
  
  if [ ! -d "venv" ]; then
    python3 -m venv venv
  fi
  source venv/bin/activate
  
  echo "Installing backend dependencies..."
  pip3 install -e .
  
  # Install variant-specific dependencies - simplified for pip
  case "$VARIANT" in
      "non-llm")
          echo "Using base dependencies (no LLM)..."
          ;;
      *)
          echo "Warning: LLM variants ($VARIANT) not fully supported with pip fallback"
          echo "Install uv for complete variant support: https://github.com/astral-sh/uv"
          echo "Proceeding with base dependencies..."
          ;;
  esac
  
  # Install PyInstaller
  echo "Installing PyInstaller..."
  pip3 install pyinstaller
  
  # Build executable
  echo "Building executable..."
  PYTHON_RUN="python3 -m"
fi

DATA_ARGS="--add-data ../frontend/build:frontend"

OUTPUT_NAME="midori-autofighter-$VARIANT-$PLATFORM"

echo "Building: $OUTPUT_NAME"
$PYTHON_RUN pyinstaller --onefile $DATA_ARGS --clean --name "$OUTPUT_NAME" app.py

echo "Build completed successfully!"
echo "Output: dist/$OUTPUT_NAME"
echo "Size: $(du -h dist/$OUTPUT_NAME | cut -f1)"