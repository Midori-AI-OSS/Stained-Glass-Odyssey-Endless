"""Custom logging handlers for battle logs."""

import logging
from logging.handlers import MemoryHandler
from logging.handlers import QueueListener
import threading


class TimedMemoryHandler(MemoryHandler):
    """Memory handler that flushes to a target on a timed interval."""

    def __init__(
        self,
        target: logging.Handler,
        flush_interval: float = 15.0,
        capacity: int = 1024,
    ) -> None:
        super().__init__(capacity=capacity, target=target)
        self.flush_interval = flush_interval
        self._timer = threading.Timer(self.flush_interval, self.flush)
        self._timer.daemon = True
        self._timer.start()

    def flush(self) -> None:  # type: ignore[override]
        self.acquire()
        try:
            super().flush()
            if not self._closed:
                self._timer.cancel()
                self._timer = threading.Timer(self.flush_interval, self.flush)
                self._timer.daemon = True
                self._timer.start()
        finally:
            self.release()

    def close(self) -> None:  # type: ignore[override]
        self._timer.cancel()
        self.acquire()
        try:
            super().flush()
        finally:
            self.release()
        super().close()


class AsyncQueueListener(QueueListener):
    """QueueListener that runs its worker thread as a daemon."""

    def start(self) -> None:  # type: ignore[override]
        thread = threading.Thread(target=self._monitor, daemon=True)
        thread.start()
        self._thread = thread


__all__ = [
    "TimedMemoryHandler",
    "AsyncQueueListener",
]

