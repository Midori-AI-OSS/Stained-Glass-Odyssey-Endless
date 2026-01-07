from __future__ import annotations

import asyncio
from enum import StrEnum
from typing import TypeVar

from async_db_utils import async_execute
from async_db_utils import async_query

OptionValue = TypeVar("OptionValue")


class OptionKey(StrEnum):
    LRM_MODEL = "lrm_model"
    LRM_BACKEND = "lrm_backend"
    LRM_API_URL = "lrm_api_url"
    LRM_API_KEY = "lrm_api_key"
    TURN_PACING = "turn_pacing"
    CONCISE_DESCRIPTIONS = "concise_descriptions"


async def get_option(key: OptionKey | str, default: OptionValue | None = None) -> str | OptionValue | None:
    """Get configuration option from database (async-safe).

    Args:
        key: Option key to retrieve (OptionKey enum or string)
        default: Default value if option not found

    Returns:
        Option value as string, or default if not found

    Raises:
        DatabaseError: If database operations fail
    """
    # Import lazily to avoid circular import during module initialization
    from runs.encryption import get_save_manager

    save_mgr = get_save_manager()

    # Ensure table exists (idempotent)
    await async_execute(
        save_mgr,
        "CREATE TABLE IF NOT EXISTS options (key TEXT PRIMARY KEY, value TEXT)"
    )

    # Query for value
    rows = await async_query(
        save_mgr,
        "SELECT value FROM options WHERE key = ?",
        (str(key),)
    )

    if not rows:
        return default
    return rows[0][0]


async def set_option(key: OptionKey | str, value: str) -> None:
    """Set configuration option in database (async-safe).

    Args:
        key: Option key to set (OptionKey enum or string)
        value: Value to store (will be converted to string)

    Raises:
        DatabaseError: If database operations fail
        ValueError: If value cannot be serialized
    """
    # Import lazily to avoid circular import during module initialization
    from runs.encryption import get_save_manager

    save_mgr = get_save_manager()

    # Ensure table exists
    await async_execute(
        save_mgr,
        "CREATE TABLE IF NOT EXISTS options (key TEXT PRIMARY KEY, value TEXT)"
    )

    # Insert or update value
    await async_execute(
        save_mgr,
        "INSERT OR REPLACE INTO options (key, value) VALUES (?, ?)",
        (str(key), str(value))
    )


# Sync wrappers for backward compatibility with non-async contexts
def get_option_sync(key: OptionKey | str, default: OptionValue | None = None) -> str | OptionValue | None:
    """Synchronous wrapper for get_option (uses asyncio.to_thread for safety).

    This should only be used in contexts where async is not available.
    Prefer using the async version when possible.

    Args:
        key: Option key to retrieve (OptionKey enum or string)
        default: Default value if option not found

    Returns:
        Option value as string, or default if not found
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # We're in an async context - this shouldn't be called
            # Fall back to creating a new thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, get_option(key, default))
                return future.result()
        else:
            return asyncio.run(get_option(key, default))
    except RuntimeError:
        # No event loop, safe to create one
        return asyncio.run(get_option(key, default))


def set_option_sync(key: OptionKey | str, value: str) -> None:
    """Synchronous wrapper for set_option (uses asyncio.to_thread for safety).

    This should only be used in contexts where async is not available.
    Prefer using the async version when possible.

    Args:
        key: Option key to set (OptionKey enum or string)
        value: Value to store (will be converted to string)
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # We're in an async context - this shouldn't be called
            # Fall back to creating a new thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, set_option(key, value))
                return future.result()
        else:
            asyncio.run(set_option(key, value))
    except RuntimeError:
        # No event loop, safe to create one
        asyncio.run(set_option(key, value))
