"""Battle logging queue system for async-friendly combat message handling."""

from __future__ import annotations

import logging
import queue
import threading

log = logging.getLogger(__name__)

_COMBAT_LOG_QUEUE: "queue.Queue[tuple[str, tuple, dict]]" = queue.Queue()


def _combat_log_worker() -> None:
    """Worker thread function that processes combat log messages."""
    while True:
        message, args, kwargs = _COMBAT_LOG_QUEUE.get()
        if message is None:
            break
        log.info(message, *args, **kwargs)
        _COMBAT_LOG_QUEUE.task_done()


# Start the combat log worker thread
_COMBAT_LOG_THREAD = threading.Thread(target=_combat_log_worker, daemon=True)
_COMBAT_LOG_THREAD.start()


def queue_log(message: str, *args, **kwargs) -> None:
    """
    Queue a combat log message for async processing.

    Args:
        message: The log message format string
        *args: Positional arguments for the message
        **kwargs: Keyword arguments for the message
    """
    _COMBAT_LOG_QUEUE.put((message, args, kwargs))


def shutdown_logging_queue() -> None:
    """Shutdown the combat logging queue gracefully."""
    _COMBAT_LOG_QUEUE.put((None, (), {}))
    _COMBAT_LOG_THREAD.join(timeout=1.0)
