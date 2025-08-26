#!/bin/bash

set -e

echo "Starting test run"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Backend tests
echo "Starting backend tests..."

# Check if uv is available, fallback to python/pytest if not
if command_exists uv; then
    echo "Using uv for backend tests"
    cd backend
    for test_file in tests/test_*.py; do
        if [[ -f "$test_file" ]]; then
            test_name=$(basename "$test_file")
            echo "Running backend test: $test_name"
            if ! timeout 25 uv run pytest "$test_file" --tb=short; then
                echo "FAILED: backend $test_file" >> ../failed_tests.log
            fi
        fi
    done
    cd ..
else
    echo "uv not found, using python -m pytest for backend tests"
    cd backend
    # Try to install basic dependencies if not present
    if ! python3 -c "import pytest" &> /dev/null; then
        echo "Installing pytest..."
        python3 -m pip install --user pytest pytest-asyncio
    fi
    
    for test_file in tests/test_*.py; do
        if [[ -f "$test_file" ]]; then
            test_name=$(basename "$test_file")
            echo "Running backend test: $test_name"
            if ! timeout 25 python3 -m pytest "$test_file" --tb=short; then
                echo "FAILED: backend $test_file" >> ../failed_tests.log
            fi
        fi
    done
    cd ..
fi

echo "Finished backend tests"

# Frontend tests  
echo "Starting frontend tests..."

# Check if bun is available, fallback to npm if available
if command_exists bun; then
    echo "Using bun for frontend tests"
    cd frontend
    for test_file in tests/*.test.js; do
        if [[ -f "$test_file" ]]; then
            test_name=$(basename "$test_file")
            echo "Running frontend test: $test_name"
            if ! timeout 25 bun test "$test_file"; then
                echo "FAILED: frontend $test_file" >> ../failed_tests.log
            fi
        fi
    done
    cd ..
elif command_exists npm; then
    echo "bun not found, attempting to use npm for frontend tests"
    cd frontend
    if [[ -f "package.json" ]]; then
        if ! timeout 25 npm test; then
            echo "FAILED: frontend npm test" >> ../failed_tests.log
        fi
    else
        echo "No package.json found, skipping npm tests"
        for test_file in tests/*.test.js; do
            if [[ -f "$test_file" ]]; then
                test_name=$(basename "$test_file")
                echo "SKIPPED: frontend $test_file (no npm test configuration)"
                echo "SKIPPED: frontend $test_file" >> ../failed_tests.log
            fi
        done
    fi
    cd ..
else
    echo "Neither bun nor npm found, skipping frontend tests"
    cd frontend
    for test_file in tests/*.test.js; do
        if [[ -f "$test_file" ]]; then
            test_name=$(basename "$test_file")
            echo "SKIPPED: frontend $test_name (no test runner available)"
            echo "SKIPPED: frontend $test_file" >> ../failed_tests.log
        fi
    done
    cd ..
fi

echo "Finished frontend tests"

# Check for failed tests
if [[ -f "failed_tests.log" ]]; then
    echo "Failed tests:"
    cat failed_tests.log
    rm failed_tests.log
    echo "Test run complete: failure"
    exit 1
else
    echo "Test run complete: success"
    exit 0
fi

