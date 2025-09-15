"""Timing helpers for battle pacing and extra turn management."""

from __future__ import annotations

import asyncio

from autofighter.action_queue import ActionQueue
from autofighter.stats import BUS
from autofighter.stats import Stats

TURN_PACING = 0.5

_EXTRA_TURNS: dict[int, int] = {}
_VISUAL_QUEUE: ActionQueue | None = None


def _grant_extra_turn(entity: Stats) -> None:
    ident = id(entity)
    _EXTRA_TURNS[ident] = _EXTRA_TURNS.get(ident, 0) + 1
    try:
        if _VISUAL_QUEUE is not None:
            _VISUAL_QUEUE.grant_extra_turn(entity)
    except Exception:
        pass


def _clear_extra_turns(_entity: Stats) -> None:
    _EXTRA_TURNS.clear()
    set_visual_queue(None)


BUS.subscribe("extra_turn", _grant_extra_turn)
BUS.subscribe("battle_end", _clear_extra_turns)


def set_visual_queue(queue: ActionQueue | None) -> None:
    """Assign the visual action queue used for rendering."""
    global _VISUAL_QUEUE
    _VISUAL_QUEUE = queue


async def _pace(start_time: float) -> None:
    """Yield control to maintain consistent pacing between actions."""
    try:
        elapsed = asyncio.get_event_loop().time() - start_time
    except Exception:
        elapsed = 0.0

    base_wait = TURN_PACING
    wait = base_wait - elapsed
    if wait > 0:
        try:
            await asyncio.sleep(wait)
        except Exception:
            pass
    try:
        await asyncio.sleep(TURN_PACING)
    except Exception:
        pass
