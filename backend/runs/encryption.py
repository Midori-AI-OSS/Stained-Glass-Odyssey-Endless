"""Run encryption and save-manager helpers."""

from __future__ import annotations

import base64
import hashlib
from pathlib import Path
import random

from cryptography.fernet import Fernet

from autofighter.save_manager import SaveManager

SAVE_MANAGER: SaveManager | None = None
FERNET: Fernet | None = None


def get_save_manager() -> SaveManager:
    """Return the global :class:`SaveManager` instance."""

    global SAVE_MANAGER
    global FERNET

    desired = SaveManager.from_env()
    if (
        SAVE_MANAGER is None
        or SAVE_MANAGER.db_path != desired.db_path
        or SAVE_MANAGER.key != desired.key
    ):
        manager = desired
        manager.migrate(Path(__file__).resolve().parent.parent / "migrations")
        with manager.connection() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS damage_types (id TEXT PRIMARY KEY, type TEXT)"
            )
            count = conn.execute("SELECT COUNT(*) FROM owned_players").fetchone()[0]
            if count == 1:
                persona = random.choice(["lady_darkness", "lady_light"])
                conn.execute("INSERT INTO owned_players (id) VALUES (?)", (persona,))

        SAVE_MANAGER = manager

        key = base64.urlsafe_b64encode(
            hashlib.sha256((manager.key or "plaintext").encode()).digest()
        )
        FERNET = Fernet(key)

    return SAVE_MANAGER


def get_fernet() -> Fernet:
    """Return the global :class:`Fernet` instance."""

    if FERNET is None:
        get_save_manager()
    assert FERNET is not None
    return FERNET


__all__ = ["get_save_manager", "get_fernet", "SaveManager", "Fernet"]

