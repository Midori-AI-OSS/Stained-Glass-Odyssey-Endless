# Error Handling and Shutdown

`request_shutdown()` provides a safe shutdown path for the backend. The
coroutine cancels active tasks, flushes queued log records, shuts down the Quart
application, and stops the running event loop.

Battle errors and unhandled exceptions invoke this helper automatically so the
server exits instead of continuing in a bad state. When debugging, you can
trigger the same behavior manually:

```python
from app import request_shutdown
await request_shutdown()
```

Using this helper ensures buffered logs are written to disk before the process
terminates.
