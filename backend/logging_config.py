import logging
from logging.handlers import MemoryHandler
from logging.handlers import QueueHandler
from logging.handlers import QueueListener
from logging.handlers import RotatingFileHandler
from pathlib import Path
import queue
import threading

from rich.logging import RichHandler


class TimedMemoryHandler(MemoryHandler):
    """Memory-buffered log handler with periodic time-based flushing.

    Extends MemoryHandler to automatically flush buffered logs at regular
    intervals, preventing memory buildup and ensuring timely log persistence.
    """
    def __init__(self, capacity: int, target: logging.Handler, flush_interval: float = 15.0) -> None:
        """Initialize timed memory handler with buffering and flush interval.

        Args:
            capacity: Maximum number of log records to buffer before forced flush.
            target: Target handler to receive flushed log records.
            flush_interval: Time in seconds between automatic flushes (default: 15.0).
        """
        super().__init__(capacity, target=target, flushLevel=logging.CRITICAL + 1)
        self.flush_interval = flush_interval
        self._timer = threading.Timer(self.flush_interval, self._flush)
        self._timer.daemon = True
        self._timer.start()

    def _flush(self) -> None:
        """Internal flush method called by timer thread.

        Flushes buffered logs and reschedules the next flush timer.
        """
        try:
            super().flush()
        finally:
            self._timer = threading.Timer(self.flush_interval, self._flush)
            self._timer.daemon = True
            self._timer.start()

    def close(self) -> None:
        """Clean up resources and flush remaining logs.

        Cancels the flush timer, flushes any remaining buffered logs,
        and closes the handler cleanly.
        """
        self._timer.cancel()
        super().flush()
        super().close()


def configure_logging() -> QueueListener:
    """Configure application logging with file rotation and console output.

    Sets up a multi-handler logging system with:
    - Rotating file handler for persistent logs (1MB files, 5 backups)
    - Timed memory buffer (15s intervals) for efficient I/O
    - Rich console handler with colored output and tracebacks
    - Queue-based async logging to prevent I/O blocking

    Returns:
        QueueListener instance that must be stopped on shutdown.
    """
    log_dir = Path(__file__).resolve().parent / "logs"
    log_dir.mkdir(exist_ok=True)

    log_queue: queue.Queue[logging.LogRecord] = queue.Queue()

    file_handler = RotatingFileHandler(
        log_dir / "backend.log", maxBytes=1_048_576, backupCount=5, delay=True
    )
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    )

    buffer_handler = TimedMemoryHandler(1024, file_handler)

    listener = QueueListener(log_queue, buffer_handler)
    listener.start()

    queue_handler = QueueHandler(log_queue)

    console_handler = RichHandler(rich_tracebacks=True)
    console_handler.setFormatter(logging.Formatter("%(message)s"))

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()
    root.addHandler(queue_handler)
    root.addHandler(console_handler)

    return listener
