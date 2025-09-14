# Error Handling and Safe Shutdown

This document describes the error handling and safe shutdown mechanisms implemented in the Midori AI AutoFighter backend.

## Overview

The backend implements a comprehensive error handling system that ensures graceful shutdown when critical errors occur. This prevents data corruption, ensures logs are properly flushed, and maintains system stability.

## Safe Shutdown Mechanism

### `shutdown_utils.py`

The core shutdown functionality is implemented in `shutdown_utils.py` which provides:

- **`request_shutdown()`**: A coroutine that performs graceful backend shutdown
- **Idempotent operation**: Multiple calls are safe and ignored
- **Testing protection**: Automatically disabled during pytest execution

### Shutdown Process

When `request_shutdown()` is called, the following sequence occurs:

1. **Logging cleanup**: Uses existing battle logging infrastructure
   - Calls `end_battle_logging("shutdown")`
   - Calls `end_run_logging()`

2. **Task cancellation**: Gracefully cancels running asyncio tasks
   - Gets all tasks except the current shutdown task
   - Cancels tasks with a 5-second timeout for graceful completion

3. **Log flushing**: Ensures all logs are written before shutdown
   - Calls `logging.shutdown()` to flush all handlers

4. **Event loop termination**: Stops the asyncio event loop
   - Schedules `loop.stop()` for the next iteration

### Error Recovery

The shutdown mechanism includes comprehensive error handling:

- Handles `TimeoutError` when tasks don't cancel within the timeout
- Handles `TypeError` for invalid task objects
- Last-resort loop stopping even if other steps fail

## Integration Points

### Battle Resolution Errors

In `game.py`, the `_run_battle` function calls `request_shutdown()` when battle resolution fails:

```python
except Exception as exc:
    state["battle"] = False
    log.exception("Battle resolution failed for %s", run_id)
    # Trigger backend shutdown after critical battle failure
    await request_shutdown()
```

This ensures that critical battle errors that could indicate corrupted game state trigger a safe shutdown.

### Unhandled Exceptions

In `app.py`, the global exception handler calls `request_shutdown()` after generating a 500 response:

```python
@app.errorhandler(Exception)
async def handle_exception(e: Exception):
    log.exception(e)
    tb = traceback.format_exc()
    response = jsonify({"error": str(e), "traceback": tb})
    response.status_code = 500
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    # Trigger backend shutdown after unhandled exception
    await request_shutdown()
    return response
```

This ensures that any unhandled exception that reaches the top level triggers a safe shutdown.

## Logging Integration

The shutdown mechanism integrates with the existing battle logging system:

- **`end_battle_logging("shutdown")`**: Finalizes any active battle logging
- **`end_run_logging()`**: Finalizes any active run logging
- **`logging.shutdown()`**: Flushes all Python logging handlers

This ensures that diagnostic information is preserved even during emergency shutdowns.

## Testing Considerations

### Automatic Test Protection

The shutdown mechanism automatically detects pytest execution via the `PYTEST_CURRENT_TEST` environment variable and skips shutdown to prevent breaking the test suite:

```python
# Skip shutdown during testing to avoid breaking tests
if os.getenv("PYTEST_CURRENT_TEST"):
    log.info("Skipping shutdown during test execution")
    return
```

### Test Coverage

The shutdown functionality is tested with:

- `test_shutdown_utils_request_shutdown`: Tests normal shutdown sequence
- `test_shutdown_utils_idempotent`: Tests that multiple calls are safe
- `test_shutdown_with_task_cancellation_timeout`: Tests timeout handling
- `test_battle_error_calls_shutdown`: Tests battle error integration

## Manual Invocation

For debugging purposes, you can manually trigger a shutdown by importing and calling the function:

```python
from shutdown_utils import request_shutdown

# In an async context
await request_shutdown()
```

This is useful for testing shutdown behavior or forcing a clean exit during development.

## Operational Benefits

### For Production

- **Data integrity**: Ensures logs are flushed before shutdown
- **Clean shutdown**: Properly cancels tasks and closes resources
- **Diagnostic preservation**: Maintains error information for debugging

### For Development

- **Predictable behavior**: Consistent shutdown process across error types
- **Debug friendly**: Comprehensive logging of shutdown steps
- **Test safe**: Automatically disabled during testing

### For Operations

- **Monitoring**: Clear log messages indicate when and why shutdown occurred
- **Recovery**: Clean shutdown allows for automatic restart without corruption
- **Diagnosis**: Preserved error information aids in root cause analysis

## Implementation Notes

### Circular Import Avoidance

The shutdown functionality is in a separate module (`shutdown_utils.py`) to avoid circular imports between `app.py` and `game.py`.

### Async Safety

The shutdown process is designed to be async-safe and handles the complexities of cancelling tasks while avoiding deadlocks.

### Production Readiness

The implementation includes comprehensive error handling to ensure shutdown succeeds even in degraded conditions.