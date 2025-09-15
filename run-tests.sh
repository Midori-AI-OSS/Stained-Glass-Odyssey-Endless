#!/bin/bash

status=0
failed_tests=()
timeout_tests=()
ROOT_DIR=$(pwd)

run_test() {
  local cmd="$1"
  local name="$2"

  # Use bash -lc so the command runs in a login shell and its stdout/stderr
  # are streamed to the current terminal (pytest -s will disable capture).
  timeout 15 bash -lc "$cmd"
  local result=$?

  if [ $result -eq 124 ]; then
    timeout_tests+=("$name")
    if [ $status -eq 0 ]; then
      status=124
    fi
  elif [ $result -ne 0 ]; then
    failed_tests+=("$name")
    if [ $status -eq 0 ]; then
      status=$result
    fi
  fi
}

# High-level start message
echo "Starting test run"

# Backend tests
cd backend

# Detect available Python tools and set up environment
if command -v uv >/dev/null 2>&1; then
  echo "Using uv for Python environment"
  if [ -n "${UV_EXTRA:-}" ]; then
    uv venv && uv sync --extra "$UV_EXTRA"
  else
    uv venv && uv sync
  fi
  PYTHON_CMD="uv run pytest"
else
  echo "uv not found, using standard Python tools"
  if [ ! -d "venv" ] || [ ! -f "venv/bin/activate" ]; then
    echo "Creating virtual environment..."
    rm -rf venv  # Clean up any partial venv
    python3 -m venv venv
    source venv/bin/activate
    echo "Installing dependencies..."
    pip3 install -e .
  else
    echo "Using existing virtual environment..."
    source venv/bin/activate
  fi
  if [ -n "${UV_EXTRA:-}" ]; then
    echo "Warning: UV_EXTRA specified but uv not available, installing base dependencies only"
  fi
  PYTHON_CMD="python3 -m pytest"
fi

echo "Starting backend tests..."
for file in $(find tests -maxdepth 1 -name "test_*.py" -type f -printf "%f\n" | sort); do
  echo "Running backend test: $file"
  run_test "$PYTHON_CMD tests/$file" "backend tests/$file"
done
echo "Finished backend tests"
cd "$ROOT_DIR"

# Frontend tests
cd frontend

# Detect available Node tools and install dependencies
if command -v bun >/dev/null 2>&1; then
  echo "Using bun for Node.js environment"
  bun install
  NODE_CMD="bun test"
  
  echo "Starting frontend tests..."
  for file in $(find tests -maxdepth 1 -name "*.test.js" -type f -printf "%f\n" | sort); do
    echo "Running frontend test: $file"
    run_test "$NODE_CMD tests/$file" "frontend tests/$file"
  done
else
  echo "bun not found, skipping frontend tests (tests require bun:test API)"
  echo "To run frontend tests, install bun: https://bun.sh/"
fi
echo "Finished frontend tests"
cd "$ROOT_DIR"

# Summary
if [ ${#failed_tests[@]} -eq 0 ] && [ ${#timeout_tests[@]} -eq 0 ]; then
  echo "All tests passed."
else
  if [ ${#failed_tests[@]} -ne 0 ]; then
    echo "Failed tests:"
    for t in "${failed_tests[@]}"; do
      echo "  $t"
    done
  fi
  if [ ${#timeout_tests[@]} -ne 0 ]; then
    echo "Timed out (>15s) tests:"
    for t in "${timeout_tests[@]}"; do
      echo "  $t"
    done
  fi
fi

# Final summary message
if [ $status -eq 0 ]; then
  echo "Test run complete: success"
else
  echo "Test run complete: failure"
fi

exit $status

