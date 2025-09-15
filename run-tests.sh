#!/bin/bash
set -o pipefail

status=0
failed_tests=()
timeout_tests=()
ROOT_DIR=$(pwd)

run_test() {
  local cmd="$1"
  local name="$2"
  local fallback_cmd="${3:-}"

  # Use bash -lc so the command runs in a login shell and its stdout/stderr
  # are streamed to the current terminal (pytest -s will disable capture).
  timeout 15 bash -lc "$cmd"
  local result=$?

  # Optional fallback path (e.g., run locally if Docker fails)
  if [ $result -ne 0 ] && [ -n "$fallback_cmd" ]; then
    echo "[fallback] Primary command failed for $name. Trying fallback..."
    timeout 15 bash -lc "$fallback_cmd"
    result=$?
  fi

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

# Optional: run backend tests inside Docker
if command -v docker >/dev/null 2>&1; then
  echo "[docker] Docker available: running backend tests in Docker"

  # For security and reproducibility, only use the fixed pixelarch image and always pull it.
  DOCKER_IMAGE="lunamidori5/pixelarch:quartz"
  docker_image_source="none"

  echo "[docker] Pulling image: $DOCKER_IMAGE"
  echo "+ docker pull \"$DOCKER_IMAGE\""
  docker pull "$DOCKER_IMAGE"
  docker_image_source="pulled"
  
  echo "[docker] Preparing image '$DOCKER_IMAGE' to ensure 'uv' and 'bun' are available inside container"
  
  # Use yay (Arch AUR helper) inside pixelarch image to install packages used by tests
  docker run --rm -i -v "$ROOT_DIR":/workspace:rw -w /workspace "$DOCKER_IMAGE" bash -s <<'EOF'
set -e
echo "[docker][install] running prep inside container"
echo "[docker][install] yay: installing uv and bun-bin via yay"
yay -S --noconfirm uv bun-bin || true

echo "[docker][install] prepare finished"
EOF
  fi

  # If fallback requested, prepare local env now
  LOCAL_PYTHON_CMD=""
  if [ "${RUN_LOCAL_ON_DOCKER_FAIL:-0}" = "1" ]; then
    echo "[docker] RUN_LOCAL_ON_DOCKER_FAIL=1: preparing local Python env for fallback"
    if command -v uv >/dev/null 2>&1; then
      echo "Using uv for Python environment (fallback)"
      if [ -n "${UV_EXTRA:-}" ]; then
        uv venv && uv sync --extra "$UV_EXTRA"
      else
        uv venv && uv sync
      fi
      LOCAL_PYTHON_CMD="uv run pytest"
    else
      echo "uv not found, using standard Python tools (fallback)"
      if [ ! -d "venv" ] || [ ! -f "venv/bin/activate" ]; then
        echo "Creating virtual environment (fallback)..."
        rm -rf venv
        python3 -m venv venv
        # shellcheck disable=SC1091
        source venv/bin/activate
        echo "Installing dependencies (fallback)..."
        pip3 install -e .
      else
        echo "Using existing virtual environment (fallback)..."
        # shellcheck disable=SC1091
        source venv/bin/activate
      fi
      if [ -n "${UV_EXTRA:-}" ]; then
        echo "Warning: UV_EXTRA specified but uv not available, installing base dependencies only (fallback)"
      fi
      LOCAL_PYTHON_CMD="python3 -m pytest"
    fi
  fi

  echo "[docker] Test container will mount: $ROOT_DIR -> /workspace"
  echo "[docker] Working directory inside container: /workspace/backend"
  PYTHON_CMD="docker run --rm -u $(id -u):$(id -g) -v \"$ROOT_DIR\":/workspace:rw -w /workspace/backend \"$DOCKER_IMAGE\" pytest -q -s --maxfail=1"
else
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
fi

echo "Starting backend tests..."
for file in $(find tests -maxdepth 1 -name "test_*.py" -type f -printf "%f\n" | sort); do
  echo "Running backend test: $file"
  if [ "${USE_DOCKER:-0}" != "0" ] && command -v docker >/dev/null 2>&1; then
    if [ "${RUN_LOCAL_ON_DOCKER_FAIL:-0}" = "1" ] && [ -n "${LOCAL_PYTHON_CMD:-}" ]; then
      run_test "$PYTHON_CMD tests/$file" "backend tests/$file" "$LOCAL_PYTHON_CMD tests/$file"
    else
      run_test "$PYTHON_CMD tests/$file" "backend tests/$file"
    fi
  else
    run_test "$PYTHON_CMD tests/$file" "backend tests/$file"
  fi
done
echo "Finished backend tests"
cd "$ROOT_DIR"

# Docker cleanup (optional)
if [ "${USE_DOCKER:-0}" != "0" ] && command -v docker >/dev/null 2>&1; then
  if [ "${DOCKER_CLEANUP:-0}" = "1" ]; then
    echo "[docker] Cleanup requested (DOCKER_CLEANUP=1)"
    can_remove=0
    if [ "${docker_image_source:-none}" = "built" ]; then
      can_remove=1
    elif [ "${docker_image_source:-none}" = "pulled" ] && [ "${DOCKER_CLEANUP_FORCE:-0}" = "1" ]; then
      can_remove=1
    fi
    if [ $can_remove -eq 1 ]; then
      echo "+ docker image rm \"${DOCKER_IMAGE:-endless-autofighter/backend-tests:local}\" || true"
      docker image rm "${DOCKER_IMAGE:-endless-autofighter/backend-tests:local}" || true
    else
      echo "[docker] Skipping image removal (pulled image and DOCKER_CLEANUP_FORCE!=1)"
    fi
    echo "+ docker image prune -f"
    docker image prune -f >/dev/null 2>&1 || true
  fi
fi

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
