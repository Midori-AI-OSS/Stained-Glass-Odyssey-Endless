"""Enrage threshold helpers for battle rooms."""

from __future__ import annotations

import asyncio
from types import ModuleType
from typing import TYPE_CHECKING

ENRAGE_TURNS_NORMAL = 100
ENRAGE_TURNS_BOSS = 500

if TYPE_CHECKING:
    from .. import Room


def _resolve_overrides(
    rooms_module: ModuleType,
    default_normal: int,
    default_boss: int,
) -> tuple[int, int]:
    """Extract enrage overrides from the rooms module."""

    normal = getattr(rooms_module, "ENRAGE_TURNS_NORMAL", default_normal)
    boss = getattr(rooms_module, "ENRAGE_TURNS_BOSS", default_boss)
    return normal, boss


async def compute_enrage_threshold(room: Room) -> int:
    """Compute the enrage threshold for the given room."""

    base_normal = ENRAGE_TURNS_NORMAL
    base_boss = ENRAGE_TURNS_BOSS

    try:
        from autofighter import rooms as rooms_module
    except Exception:  # pragma: no cover - defensive against dynamic loaders
        rooms_module = None

    if rooms_module is not None:
        base_normal, base_boss = await asyncio.to_thread(
            _resolve_overrides,
            rooms_module,
            base_normal,
            base_boss,
        )

    boss_type = None
    if rooms_module is not None:
        boss_type = getattr(rooms_module, "BossRoom", None)

    if boss_type is None:
        from ..boss import BossRoom  # imported lazily to avoid circular imports

        boss_type = BossRoom

    return base_boss if isinstance(room, boss_type) else base_normal


__all__ = [
    "ENRAGE_TURNS_NORMAL",
    "ENRAGE_TURNS_BOSS",
    "compute_enrage_threshold",
]
