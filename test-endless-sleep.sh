#!/bin/bash
#
# test-endless-sleep.sh - Demonstrates what happens when running endless-sleep.sh
#
# This script shows the different behaviors and outcomes when running a script
# that sleeps indefinitely, including:
# - Running with timeout (controlled termination)
# - Running in background and killing manually
# - Understanding exit codes
#

set -e

echo "======================================================================"
echo "Testing Endless Sleep Script - Behavior Demonstration"
echo "======================================================================"
echo ""

# Test 1: Run with timeout
echo "TEST 1: Running endless-sleep.sh with 15-second timeout"
echo "----------------------------------------------------------------------"
echo "Command: timeout 15 ./endless-sleep.sh"
echo ""

timeout 15 ./endless-sleep.sh || exit_code=$?

echo ""
if [ ${exit_code:-0} -eq 124 ]; then
    echo "✓ Result: Script was terminated by timeout after 15 seconds"
    echo "  Exit code: 124 (timeout signal)"
    echo "  This is the expected behavior when a long-running process exceeds its timeout."
else
    echo "✗ Result: Unexpected exit code: ${exit_code:-0}"
fi

echo ""
echo "======================================================================"
echo ""

# Test 2: Run in background and kill
echo "TEST 2: Running endless-sleep.sh in background and killing manually"
echo "----------------------------------------------------------------------"
echo "Starting endless-sleep.sh in background..."

./endless-sleep.sh > /tmp/endless-sleep-output.txt 2>&1 &
pid=$!

echo "Process started with PID: $pid"
echo "Waiting 5 seconds..."
sleep 5

echo "Killing process $pid..."
kill $pid
wait $pid 2>/dev/null || exit_code=$?

echo ""
if [ ${exit_code:-0} -eq 143 ]; then
    echo "✓ Result: Script was terminated by SIGTERM signal"
    echo "  Exit code: 143 (128 + 15 where 15 is SIGTERM)"
    echo "  This is the expected behavior when manually killing a process."
elif [ ${exit_code:-0} -eq 0 ]; then
    echo "✓ Result: Script terminated cleanly"
    echo "  Exit code: 0"
else
    echo "✓ Result: Script was terminated"
    echo "  Exit code: ${exit_code:-0}"
fi

echo ""
echo "Output from background run:"
head -20 /tmp/endless-sleep-output.txt
echo ""

rm -f /tmp/endless-sleep-output.txt

echo "======================================================================"
echo ""

# Summary
echo "SUMMARY: What happens when you run an endlessly sleeping shell script?"
echo "----------------------------------------------------------------------"
echo ""
echo "1. WITHOUT TIMEOUT:"
echo "   - The script runs indefinitely until manually stopped"
echo "   - It blocks the terminal and prevents other commands from running"
echo "   - You must press Ctrl+C or kill the process from another terminal"
echo ""
echo "2. WITH TIMEOUT (e.g., 'timeout 10 ./endless-sleep.sh'):"
echo "   - The script runs for the specified duration (10 seconds)"
echo "   - The timeout command sends SIGTERM after the time expires"
echo "   - Exit code is 124, indicating timeout occurred"
echo "   - Control returns to the shell automatically"
echo ""
echo "3. BACKGROUND WITH MANUAL KILL:"
echo "   - Script runs in background without blocking terminal"
echo "   - Must be killed manually with 'kill <pid>'"
echo "   - Exit code is 143 (SIGTERM) or other termination signal"
echo ""
echo "4. PRACTICAL IMPLICATIONS:"
echo "   - Long-running scripts should have timeouts in CI/CD pipelines"
echo "   - The run-tests.sh script uses 15-second timeouts for this reason"
echo "   - Scripts should handle SIGTERM gracefully for clean shutdown"
echo "   - Always use timeout or background execution for potentially"
echo "     infinite processes to avoid blocking your workflow"
echo ""
echo "======================================================================"
echo "Test completed successfully!"
