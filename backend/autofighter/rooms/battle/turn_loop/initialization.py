from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import Any
from typing import Awaitable
from typing import Callable

from autofighter.stats import BUS

from ..pacing import _EXTRA_TURNS
from ..pacing import TURN_PACING
from ..pacing import pace_sleep
from ..turns import prepare_snapshot_overlay
from ..turns import push_progress_update
from ..turns import register_snapshot_entities

if TYPE_CHECKING:
    from asyncio import Task

    from autofighter.effects import EffectManager

    from ...party import Party
    from ..core import BattleRoom
    from ..turns import EnrageState


@dataclass
class TurnLoopContext:
    """Shared data structure used while processing the battle turn loop."""

    room: BattleRoom
    party: Party
    combat_party: Party
    registry: Any
    foes: list[Any]
    foe_effects: list[EffectManager]
    enrage_mods: list[Any]
    enrage_state: EnrageState
    progress: Callable[[dict[str, Any]], Awaitable[None]] | None
    visual_queue: Any
    temp_rdr: float
    exp_reward: int
    run_id: str | None
    battle_tasks: dict[str, Task[Any]]
    abort: Callable[[str], None]
    credited_foe_ids: set[str]
    turn: int

    @property
    def credit_kwargs(self) -> dict[str, Any]:
        return {
            "credited_foe_ids": self.credited_foe_ids,
            "combat_party": self.combat_party,
            "party": self.party,
            "room": self.room,
        }


async def initialize_turn_loop(
    *,
    room: BattleRoom,
    party: Party,
    combat_party: Party,
    registry: Any,
    foes: list[Any],
    foe_effects: list[EffectManager],
    enrage_mods: list[Any],
    enrage_state: EnrageState,
    progress: Callable[[dict[str, Any]], Awaitable[None]] | None,
    visual_queue: Any,
    temp_rdr: float,
    exp_reward: int,
    run_id: str | None,
    battle_tasks: dict[str, Task[Any]],
    abort: Callable[[str], None],
) -> TurnLoopContext:
    """Prepare the turn loop context and emit the initial progress update."""

    context = TurnLoopContext(
        room=room,
        party=party,
        combat_party=combat_party,
        registry=registry,
        foes=foes,
        foe_effects=foe_effects,
        enrage_mods=enrage_mods,
        enrage_state=enrage_state,
        progress=progress,
        visual_queue=visual_queue,
        temp_rdr=temp_rdr,
        exp_reward=exp_reward,
        run_id=run_id,
        battle_tasks=battle_tasks,
        abort=abort,
        credited_foe_ids=set(),
        turn=0,
    )

    prepare_snapshot_overlay(
        context.run_id,
        [
            context.party,
            context.combat_party,
            *list(context.combat_party.members),
            *list(context.foes),
        ],
    )
    await _prepare_entities(context)
    await _send_initial_progress(context)
    return context


async def _prepare_entities(context: TurnLoopContext) -> None:
    """Set action point counts and emit extra turn events for all entities."""

    register_snapshot_entities(
        context.run_id,
        [context.party, context.combat_party],
    )
    for entity in list(context.combat_party.members) + list(context.foes):
        entity.action_points = entity.actions_per_turn
        register_snapshot_entities(context.run_id, [entity])
        for _ in range(max(0, entity.action_points - 1)):
            try:
                await BUS.emit_async("extra_turn", entity)
            except Exception:
                pass


async def _send_initial_progress(context: TurnLoopContext) -> None:
    """Emit the initial progress update if a progress callback is provided."""

    if context.progress is None:
        return

    await push_progress_update(
        context.progress,
        context.combat_party.members,
        context.foes,
        context.enrage_state,
        context.temp_rdr,
        _EXTRA_TURNS,
        context.turn,
        run_id=context.run_id,
        active_id=None,
        active_target_id=None,
        include_summon_foes=True,
        visual_queue=context.visual_queue,
    )
    await pace_sleep(3 / TURN_PACING)
