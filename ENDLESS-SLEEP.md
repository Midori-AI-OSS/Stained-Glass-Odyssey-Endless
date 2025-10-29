# Endless Sleep Script with Ollama Integration

This directory contains scripts that demonstrate what happens when you create and run a shell script that sleeps indefinitely, now enhanced with Ollama LLM integration for practical use cases.

## Files

### `endless-sleep.sh`
A script that runs an infinite loop, sleeping indefinitely until interrupted or killed. Now includes:
- **Ollama Installation**: Automatically installs Ollama if not present
- **Model Setup**: Pulls and prepares the `gpt-oss:20b` model
- **Heartbeat System**: Sends a heartbeat to Ollama every 60 seconds with "say hi" prompt

**Usage:**
```bash
# Run indefinitely with Ollama integration (press Ctrl+C to stop)
./endless-sleep.sh

# Run with a timeout (automatically stops after N seconds)
timeout 120 ./endless-sleep.sh

# Run in background
./endless-sleep.sh &
```

**Features:**
- Checks for Ollama installation and installs if needed
- Starts Ollama service automatically
- Pulls `gpt-oss:20b` model on first run
- Sends heartbeat every 60 seconds to keep model active
- Displays elapsed time every second

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
- **LLM Model Availability:** Keep models warm and ready for user requests
- **Heartbeat Systems:** Demonstrate periodic service health checks

## Exit Codes

- **0:** Normal termination (script completed)
- **124:** Timeout signal (timeout command limit reached)
- **143:** SIGTERM (128 + 15, manual termination)
- **130:** SIGINT (128 + 2, Ctrl+C pressed)

## Ollama Integration

The script now includes Ollama integration for practical LLM use cases:

### Setup Process
1. **Check for Ollama**: Verifies if Ollama is installed
2. **Install if Needed**: Automatically installs Ollama using official installer
3. **Start Service**: Launches Ollama service in background
4. **Pull Model**: Downloads `gpt-oss:20b` model (20 billion parameters)
5. **Ready to Use**: Model is warmed up and ready for requests

### Heartbeat System
- Every **60 seconds**, the script sends a heartbeat to the Ollama model
- Prompt: "say hi" with high reasoning enabled
- Keeps the model active and warm in memory
- Demonstrates periodic LLM interaction patterns

### Use Cases
- **Model Availability**: Ensure LLM is always ready for user requests
- **Service Monitoring**: Verify Ollama service health periodically
- **Development Testing**: Keep model loaded during development sessions
- **Warm-up Automation**: Prevent cold-start delays for first requests

## Real-World Examples

This repository already uses timeout patterns:
- `run-tests.sh`: Uses 15-second timeouts for test execution
- `build.sh`: LLM builds can take 10+ minutes (needs long timeout)
- CI/CD: Automated pipelines need timeout protection

## Try It Yourself

```bash
# Quick test - see timeout in action (won't complete Ollama setup)
timeout 5 ./endless-sleep.sh

# Let it run for 2 minutes to see first heartbeat (at 60s)
timeout 120 ./endless-sleep.sh

# Full demonstration with test script
./test-endless-sleep.sh
```

## Requirements

- **curl**: For downloading Ollama installer
- **bash**: Shell environment
- **Internet connection**: For downloading Ollama and models
- **Disk space**: ~12GB for gpt-oss:20b model
