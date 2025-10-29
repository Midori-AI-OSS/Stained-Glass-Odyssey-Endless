#!/bin/bash
#
# endless-sleep.sh - A script that sleeps indefinitely
#
# This script demonstrates what happens when a shell script runs for an
# extremely long time (or forever). It's useful for understanding:
# - How timeouts work with long-running processes
# - How to handle processes that need to be killed
# - Exit codes when processes are terminated
#
# Usage:
#   ./endless-sleep.sh              # Runs forever (Ctrl+C to stop)
#   timeout 5 ./endless-sleep.sh    # Runs for 5 seconds then kills (exit 124)
#

echo "Starting endless sleep script..."
echo "This script will sleep indefinitely until killed or interrupted."
echo "Press Ctrl+C to stop, or use 'timeout' command to limit execution time."
echo ""

# Track how long we've been running
seconds=0

# Endless loop - sleeps forever
while true; do
    echo "Still sleeping... (${seconds}s elapsed)"
    sleep 1
    seconds=$((seconds + 1))
done

# This line is never reached unless the script is interrupted
echo "Sleep was interrupted!"
