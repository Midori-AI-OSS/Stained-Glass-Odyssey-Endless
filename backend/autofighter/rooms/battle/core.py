"""BattleRoom loop and high-level battle control flow."""

from __future__ import annotations

from collections.abc import Awaitable
from collections.abc import Callable
from dataclasses import dataclass
import random
from typing import Any

from autofighter.mapgen import MapNode

from ...party import Party
from .. import Room
from .engine import run_battle
from .enrage import ENRAGE_TURNS_BOSS
from .enrage import ENRAGE_TURNS_NORMAL
from .enrage import compute_enrage_threshold
from .setup import setup_battle

# Expose module-level random so existing tests can patch deterministic rolls.
random = random


@dataclass
class BattleRoom(Room):
    """Standard battle room where the party fights a group of foes."""

    node: MapNode
    strength: float = 1.0

    async def resolve(
        self,
        party: Party,
        data: dict[str, Any],
        progress: Callable[[dict[str, Any]], Awaitable[None]] | None = None,
        foe: Stats | list[Stats] | None = None,
        run_id: str | None = None,
    ) -> dict[str, Any]:
        """Resolve the battle by delegating to the async engine."""

        from runs.lifecycle import battle_snapshots
        from runs.lifecycle import battle_tasks

        start_gold = party.gold
        setup_data = await setup_battle(
            self.node,
            party,
            foe=foe,
            strength=self.strength,
        )
        threshold = await compute_enrage_threshold(self)

        return await run_battle(
            self,
            party=party,
            setup_data=setup_data,
            start_gold=start_gold,
            enrage_threshold=threshold,
            progress=progress,
            run_id=run_id,
            battle_snapshots=battle_snapshots,
            battle_tasks=battle_tasks,
        )


from ...stats import Stats  # noqa: E402  # imported for type annotations

__all__ = [
    "BattleRoom",
    "ENRAGE_TURNS_NORMAL",
    "ENRAGE_TURNS_BOSS",
]

