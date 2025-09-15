"""Enrage system and extra turns management for battle mechanics."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..action_queue import ActionQueue
    from ..stats import Stats

# Constants for enrage timing
ENRAGE_TURNS_NORMAL = 100
ENRAGE_TURNS_BOSS = 500

# Global state for extra turns and visual queue
_EXTRA_TURNS: dict[int, int] = {}
_VISUAL_QUEUE: ActionQueue | None = None


def grant_extra_turn(entity: Stats) -> None:
    """
    Grant an extra turn to the specified entity.

    Args:
        entity: The Stats entity to grant an extra turn to
    """
    ident = id(entity)
    _EXTRA_TURNS[ident] = _EXTRA_TURNS.get(ident, 0) + 1
    try:
        if _VISUAL_QUEUE is not None:
            _VISUAL_QUEUE.grant_extra_turn(entity)
    except Exception:
        pass


def clear_extra_turns(_entity: Stats) -> None:
    """
    Clear all extra turns and reset visual queue.

    Args:
        _entity: The Stats entity (unused but required for event signature)
    """
    _EXTRA_TURNS.clear()
    global _VISUAL_QUEUE
    _VISUAL_QUEUE = None


def get_extra_turns(entity: Stats) -> int:
    """
    Get the number of extra turns for an entity.

    Args:
        entity: The Stats entity to check

    Returns:
        Number of extra turns remaining for the entity
    """
    return _EXTRA_TURNS.get(id(entity), 0)


def consume_extra_turn(entity: Stats) -> bool:
    """
    Consume one extra turn for an entity.

    Args:
        entity: The Stats entity to consume a turn for

    Returns:
        True if an extra turn was consumed, False if none available
    """
    ident = id(entity)
    if _EXTRA_TURNS.get(ident, 0) > 0:
        _EXTRA_TURNS[ident] -= 1
        return True
    return False


def set_visual_queue(queue: ActionQueue | None) -> None:
    """
    Set the visual action queue for UI updates.

    Args:
        queue: The ActionQueue instance or None to clear
    """
    global _VISUAL_QUEUE
    _VISUAL_QUEUE = queue


def get_visual_queue() -> ActionQueue | None:
    """
    Get the current visual action queue.

    Returns:
        The current ActionQueue instance or None
    """
    return _VISUAL_QUEUE
