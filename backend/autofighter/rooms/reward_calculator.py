"""Reward calculation system for battle loot, gold, cards, and relics."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import Room

# Import here to avoid circular imports
def _get_boss_room_class():
    from .boss import BossRoom
    return BossRoom


def pick_card_stars(room: Room) -> int:
    """Determine the star rank for card rewards."""
    BossRoom = _get_boss_room_class()
    roll = random.random()
    if isinstance(room, BossRoom):
        if roll < 0.60:
            return 3
        if roll < 0.85:
            return 4
        return 5
    if hasattr(room, 'strength') and room.strength > 1.0:
        if roll < 0.40:
            return 1
        if roll < 0.70:
            return 2
        if roll < 0.7015:
            return 3
        if roll < 0.7025:
            return 4
        return 5
    return 1 if roll < 0.80 else 2


def roll_relic_drop(room: Room, rdr: float) -> bool:
    """Check whether a relic drops based on room type and RDR."""
    BossRoom = _get_boss_room_class()
    roll = random.random()
    base = 0.5 if isinstance(room, BossRoom) else 0.1
    return roll < min(base * rdr, 1.0)


def pick_item_stars(room: Room) -> int:
    """Select upgrade item star rank based on room difficulty."""
    BossRoom = _get_boss_room_class()
    node = room.node
    if node.room_type == "battle-boss-floor":
        low, high = 3, 4
    elif isinstance(room, BossRoom) or getattr(room, "strength", 1.0) > 1.0:
        low, high = 1, 3
    else:
        low, high = 1, 2
    base = low + (node.floor - 1) // 20 + (node.loop - 1) + node.pressure // 10
    return min(base, high)


def calc_gold(room: Room, rdr: float) -> int:
    """Calculate gold reward for the room."""
    BossRoom = _get_boss_room_class()
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


def pick_relic_stars(room: Room) -> int:
    """Pick relic star rating based on room type."""
    BossRoom = _get_boss_room_class()
    roll = random.random()
    if isinstance(room, BossRoom):
        if roll < 0.6:
            return 3
        if roll < 0.9:
            return 4
        return 5
    if roll < 0.7:
        return 1
    if roll < 0.9:
        return 2
    return 3


def apply_rdr_to_stars(stars: int, rdr: float) -> int:
    """Chance to upgrade stars with extreme `rdr` values."""
    for threshold in (10.0, 10000.0):
        if stars >= 5 or rdr < threshold:
            break
        chance = min(rdr / (threshold * 10.0), 0.99)
        if random.random() < chance:
            stars += 1
        else:
            break
    return stars
