"""Error persistence service for crash recovery.

This module provides functionality to persist errors to disk so they survive
application crashes and can be displayed to users on startup.
"""

from __future__ import annotations

import atexit
from datetime import datetime
from datetime import timezone
import json
import logging
from pathlib import Path
from typing import Any

from models.errors import ErrorResponse
from models.errors import PersistedErrors

log = logging.getLogger(__name__)

ERROR_FILE = Path("data/errors.json")
MAX_PERSISTED_ERRORS = 10

# Holds the most recent error that hasn't been flushed yet.
# This is safe in the async single-threaded Quart environment because
# Python's GIL ensures atomic assignment, and the error handler runs
# sequentially (one request at a time triggers the error handler).
_pending_error: ErrorResponse | None = None


def persist_error(error: ErrorResponse) -> None:
    """Save error to persistent storage.

    Args:
        error: The error response to persist
    """
    global _pending_error
    _pending_error = error

    try:
        ERROR_FILE.parent.mkdir(parents=True, exist_ok=True)

        existing = load_errors()
        existing.errors.append(error)
        existing.last_crash = datetime.now(timezone.utc)

        # Keep only last N errors to prevent file bloat
        existing.errors = existing.errors[-MAX_PERSISTED_ERRORS:]

        ERROR_FILE.write_text(existing.model_dump_json(indent=2))
        _pending_error = None
        log.debug("Persisted error %s to disk", error.id)
    except Exception as e:
        log.warning("Failed to persist error to disk: %s", e)


def load_errors() -> PersistedErrors:
    """Load errors from persistent storage.

    Returns:
        PersistedErrors instance with any stored errors
    """
    if not ERROR_FILE.exists():
        return PersistedErrors()

    try:
        content = ERROR_FILE.read_text()
        data = json.loads(content)
        return PersistedErrors.model_validate(data)
    except Exception as e:
        log.warning("Failed to load persisted errors: %s", e)
        return PersistedErrors()


def clear_errors() -> None:
    """Clear persisted errors after user acknowledgment."""
    global _pending_error
    _pending_error = None

    if ERROR_FILE.exists():
        try:
            ERROR_FILE.unlink()
            log.debug("Cleared persisted errors")
        except Exception as e:
            log.warning("Failed to clear persisted errors: %s", e)


def get_previous_errors() -> list[dict[str, Any]]:
    """Get list of previous errors for API response.

    Returns:
        List of error dictionaries ready for JSON serialization
    """
    persisted = load_errors()
    return [e.model_dump(mode="json") for e in persisted.errors]


def has_previous_errors() -> bool:
    """Check if there are persisted errors from a previous crash.

    Returns:
        True if there are persisted errors
    """
    persisted = load_errors()
    return len(persisted.errors) > 0


def _flush_pending_error() -> None:
    """Atexit handler to ensure pending error is written on crash.

    Note: This runs during interpreter shutdown, so logging may not work.
    We use print() as a fallback for critical issues.
    """
    global _pending_error
    if _pending_error is not None:
        try:
            ERROR_FILE.parent.mkdir(parents=True, exist_ok=True)
            existing = load_errors()
            existing.errors.append(_pending_error)
            existing.last_crash = datetime.now(timezone.utc)
            existing.errors = existing.errors[-MAX_PERSISTED_ERRORS:]
            ERROR_FILE.write_text(existing.model_dump_json(indent=2))
        except OSError as e:
            # File system errors are critical - try to report
            try:
                print(f"[error_storage] Failed to flush pending error to disk: {e}")
            except Exception:
                pass
        except Exception as e:
            # Other errors - try to report but don't crash
            try:
                print(f"[error_storage] Unexpected error during flush: {e}")
            except Exception:
                pass


# Register atexit handler to flush any pending error before process exits
atexit.register(_flush_pending_error)
