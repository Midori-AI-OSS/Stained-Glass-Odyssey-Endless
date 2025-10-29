# Endless Sleep Script Experiment

This directory contains two scripts that demonstrate what happens when you create and run a shell script that sleeps indefinitely.

## Files

### `endless-sleep.sh`
A simple script that runs an infinite loop, sleeping indefinitely until interrupted or killed.

**Usage:**
```bash
# Run indefinitely (press Ctrl+C to stop)
./endless-sleep.sh

# Run with a timeout (automatically stops after N seconds)
timeout 10 ./endless-sleep.sh

# Run in background
./endless-sleep.sh &
```

### `test-endless-sleep.sh`
A demonstration script that shows different ways to run and manage the endless-sleep script, including:
- Running with timeout
- Running in background and killing manually
- Understanding exit codes and signals

**Usage:**
```bash
./test-endless-sleep.sh
```

## What Happens?

When you run a shell script that endlessly sleeps:

### 1. Without Timeout
- The script runs indefinitely
- It blocks the terminal
- You must manually stop it with Ctrl+C or kill it from another terminal
- **Risk:** Can block CI/CD pipelines or automated workflows

### 2. With Timeout
- The script runs for the specified duration
- The `timeout` command sends SIGTERM when time expires
- Exit code is **124**, indicating timeout
- Control returns to shell automatically
- **Best practice:** Use this in automation

### 3. Background Execution
- Script runs without blocking terminal
- Must be killed manually with `kill <pid>`
- Exit code is **143** (SIGTERM) when killed
- Useful for monitoring or daemon-like processes

## Why This Matters

Understanding long-running process behavior is important for:
- **CI/CD Pipelines:** Prevent builds from hanging indefinitely
- **Testing:** The `run-tests.sh` uses 15-second timeouts
- **Resource Management:** Avoid zombie processes
- **Graceful Shutdown:** Handle SIGTERM properly

## Exit Codes

- **0:** Normal termination (script completed)
- **124:** Timeout signal (timeout command limit reached)
- **143:** SIGTERM (128 + 15, manual termination)
- **130:** SIGINT (128 + 2, Ctrl+C pressed)

## Real-World Examples

This repository already uses timeout patterns:
- `run-tests.sh`: Uses 15-second timeouts for test execution
- `build.sh`: LLM builds can take 10+ minutes (needs long timeout)
- CI/CD: Automated pipelines need timeout protection

## Try It Yourself

```bash
# Quick test - see timeout in action
timeout 5 ./endless-sleep.sh

# Full demonstration
./test-endless-sleep.sh
```
