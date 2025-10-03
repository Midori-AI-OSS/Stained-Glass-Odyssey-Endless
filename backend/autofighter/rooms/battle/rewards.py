"""Helpers for calculating battle rewards like cards and relics."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .. import Room


def _pick_card_stars(room: "Room") -> int:
    from ..boss import BossRoom
    from .core import BattleRoom

    roll = random.random()
    if isinstance(room, BossRoom):
        if roll < 0.95:
            return 3
        if roll < 0.99:
            return 4
        return 5
    if isinstance(room, BattleRoom) and getattr(room, "strength", 1.0) > 1.0:
        if roll < 0.70:
            return 1
        if roll < 0.95:
            return 2
        if roll < 0.99:
            return 3
        if roll < 0.999:
            return 4
        return 5
    return 1 if roll < 0.99 else 2


def _roll_relic_drop(room: "Room", rdr: float) -> bool:
    from ..boss import BossRoom

    roll = random.random()
    base = 0.5 if isinstance(room, BossRoom) else 0.1
    return roll < min(base * rdr, 1.0)


def _pick_item_stars(room: "Room") -> int:
    from ..boss import BossRoom

    node = room.node
    if node.room_type == "battle-boss-floor":
        low, high = 3, 4
    elif isinstance(room, BossRoom) or getattr(room, "strength", 1.0) > 1.0:
        low, high = 1, 3
    else:
        low, high = 1, 2
    base = low + (node.floor - 1) // 20 + (node.loop - 1) + node.pressure // 10
    return min(base, high)


def _calc_gold(room: "Room", rdr: float) -> int:
    from ..boss import BossRoom

    node = room.node
    if node.room_type == "battle-boss-floor":
        base = 200
        mult = random.uniform(2.05, 4.25)
    elif isinstance(room, BossRoom) or getattr(room, "strength", 1.0) > 1.0:
        base = 20
        mult = random.uniform(1.53, 2.25)
    else:
        base = 5
        mult = random.uniform(1.01, 1.25)
    return int(base * node.loop * mult * rdr)


def _pick_relic_stars(room: "Room") -> int:
    from ..boss import BossRoom

    roll = random.random()
    if isinstance(room, BossRoom):
        if roll < 0.9:
            return 3
        if roll < 0.99:
            return 4
        return 5
    if roll < 0.95:
        return 1
    if roll < 0.98:
        return 2
    return 3


def _apply_rdr_to_stars(stars: int, rdr: float) -> int:
    """Chance to upgrade stars with extreme ``rdr`` values."""
    for threshold in (10.0, 10000.0):
        if stars >= 5 or rdr < threshold:
            break
        chance = min(rdr / (threshold * 10.0), 0.99)
        if random.random() < chance:
            stars += 1
        else:
            break
    return stars
