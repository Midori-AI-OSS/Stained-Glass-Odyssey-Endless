from __future__ import annotations

from enum import StrEnum
from typing import TypeVar

OptionValue = TypeVar("OptionValue")


class OptionKey(StrEnum):
    LRM_MODEL = "lrm_model"
    TURN_PACING = "turn_pacing"


def get_option(key: OptionKey | str, default: OptionValue | None = None) -> str | OptionValue | None:
    # Import lazily to avoid circular import during module initialization
    from runs.encryption import get_save_manager

    with get_save_manager().connection() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS options (key TEXT PRIMARY KEY, value TEXT)")
        cur = conn.execute("SELECT value FROM options WHERE key = ?", (key,))
        row = cur.fetchone()
    if row is None:
        return default
    return row[0]


def set_option(key: OptionKey | str, value: str) -> None:
    # Import lazily to avoid circular import during module initialization
    from runs.encryption import get_save_manager

    with get_save_manager().connection() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS options (key TEXT PRIMARY KEY, value TEXT)")
        conn.execute("INSERT OR REPLACE INTO options (key, value) VALUES (?, ?)", (key, value))
