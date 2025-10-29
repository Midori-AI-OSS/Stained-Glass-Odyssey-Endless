#!/bin/bash
#
# endless-sleep.sh - A script that sleeps indefinitely with Ollama integration
#
# This script demonstrates what happens when a shell script runs for an
# extremely long time (or forever). It's useful for understanding:
# - How timeouts work with long-running processes
# - How to handle processes that need to be killed
# - Exit codes when processes are terminated
# - Integration with Ollama for LLM interactions
#
# Usage:
#   ./endless-sleep.sh              # Runs forever (Ctrl+C to stop)
#   timeout 5 ./endless-sleep.sh    # Runs for 5 seconds then kills (exit 124)
#

echo "Starting endless sleep script with Ollama integration..."
echo "This script will sleep indefinitely until killed or interrupted."
echo "Press Ctrl+C to stop, or use 'timeout' command to limit execution time."
echo ""

# Install Ollama if not already installed
echo "Checking for Ollama installation..."
if ! command -v ollama &> /dev/null; then
    echo "Ollama not found. Attempting installation..."
    
    # Try apt-get first (Debian/Ubuntu systems)
    if command -v apt-get &> /dev/null; then
        echo "Trying apt-get installation..."
        if sudo apt-get update -qq && sudo apt-get install -y ollama 2>&1 | grep -q "Setting up ollama"; then
            echo "✓ Ollama installed successfully via apt-get"
            OLLAMA_AVAILABLE=true
        else
            echo "  apt-get installation not available, trying official installer..."
            # Fallback to official installer
            if curl -fsSL https://ollama.com/install.sh | sh; then
                echo "✓ Ollama installed successfully via official installer"
                OLLAMA_AVAILABLE=true
            else
                echo "✗ Failed to install Ollama (network issue or unsupported system)"
                echo "  You can manually install from: https://ollama.com"
                echo "  Continuing with basic sleep functionality only..."
                OLLAMA_AVAILABLE=false
            fi
        fi
    else
        # No apt-get, try official installer
        echo "Trying official installer..."
        if curl -fsSL https://ollama.com/install.sh | sh; then
            echo "✓ Ollama installed successfully"
            OLLAMA_AVAILABLE=true
        else
            echo "✗ Failed to install Ollama (network issue or unsupported system)"
            echo "  You can manually install from: https://ollama.com"
            echo "  Continuing with basic sleep functionality only..."
            OLLAMA_AVAILABLE=false
        fi
    fi
else
    echo "✓ Ollama is already installed"
    OLLAMA_AVAILABLE=true
fi

# Only proceed with Ollama setup if available
if [ "${OLLAMA_AVAILABLE}" != "false" ]; then
    # Start Ollama service in background if not running
    echo "Starting Ollama service..."
    if ! pgrep -x "ollama" > /dev/null; then
        ollama serve > /tmp/ollama-serve.log 2>&1 &
        sleep 5  # Give it time to start
        echo "✓ Ollama service started"
    else
        echo "✓ Ollama service is already running"
    fi

    # Pull the gpt-oss:20b model
    echo "Pulling gpt-oss:20b model..."
    if ollama pull gpt-oss:20b; then
        echo "✓ Model gpt-oss:20b pulled successfully"
    else
        echo "✗ Failed to pull model gpt-oss:20b"
        echo "  Continuing with basic sleep functionality only..."
        OLLAMA_AVAILABLE=false
    fi
fi

echo ""
echo "Setup complete! Starting endless sleep loop with heartbeat..."
echo ""

# Track how long we've been running
seconds=0

# Endless loop - sleeps and sends heartbeat every 60 seconds
while true; do
    echo "Still sleeping... (${seconds}s elapsed)"
    
    # Every 60 seconds, send a heartbeat to Ollama (if available)
    if [ "${OLLAMA_AVAILABLE}" != "false" ] && [ $((seconds % 60)) -eq 0 ] && [ $seconds -gt 0 ]; then
        echo "  → Sending heartbeat to Ollama (gpt-oss:20b) with high reasoning..."
        response=$(ollama run gpt-oss:20b "say hi" 2>&1)
        echo "  ← Ollama response: $response"
    fi
    
    sleep 1
    seconds=$((seconds + 1))
done

# This line is never reached unless the script is interrupted
echo "Sleep was interrupted!"
