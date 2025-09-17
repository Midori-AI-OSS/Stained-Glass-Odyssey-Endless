"""Utilities for queuing combat log messages on a background thread."""

from __future__ import annotations

import logging
import queue
import threading

log = logging.getLogger(__name__)

_COMBAT_LOG_QUEUE: "queue.Queue[tuple[str, tuple, dict]]" = queue.Queue()


def _combat_log_worker() -> None:
    while True:
        message, args, kwargs = _COMBAT_LOG_QUEUE.get()
        if message is None:
            break
        log.info(message, *args, **kwargs)
        _COMBAT_LOG_QUEUE.task_done()


_COMBAT_LOG_THREAD = threading.Thread(target=_combat_log_worker, daemon=True)
_COMBAT_LOG_THREAD.start()


def queue_log(message: str, *args, **kwargs) -> None:
    """Add a message to the combat log queue."""
    _COMBAT_LOG_QUEUE.put((message, args, kwargs))
