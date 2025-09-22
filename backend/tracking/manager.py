"""Factory helpers for the tracking database."""
from __future__ import annotations

from pathlib import Path

from .db import TrackingDBManager

TRACKING_MANAGER: TrackingDBManager | None = None


def get_tracking_manager() -> TrackingDBManager:
    """Return a cached :class:`TrackingDBManager` instance."""

    global TRACKING_MANAGER

    desired = TrackingDBManager.from_env()
    if (
        TRACKING_MANAGER is None
        or TRACKING_MANAGER.db_path != desired.db_path
        or TRACKING_MANAGER.key != desired.key
    ):
        manager = desired
        migrations = Path(__file__).resolve().parent / "migrations"
        manager.migrate(migrations)
        TRACKING_MANAGER = manager
    return TRACKING_MANAGER


__all__ = ["get_tracking_manager", "TrackingDBManager"]
