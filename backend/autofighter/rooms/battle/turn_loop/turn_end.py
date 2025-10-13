from __future__ import annotations

from typing import Any

from ..pacing import _EXTRA_TURNS
from ..pacing import YIELD_MULTIPLIER
from ..pacing import _pace
from ..pacing import pace_sleep
from ..turns import canonical_entity_pair
from ..turns import dispatch_turn_end_snapshot
from ..turns import push_progress_update
from .initialization import TurnLoopContext


async def finish_turn(
    context: TurnLoopContext,
    actor: Any,
    action_start: float,
    *,
    include_summon_foes: bool = False,
    active_target_id: str | None = None,
    legacy_active_target_id: str | None = None,
    spent_override: float | None = None,
) -> None:
    """Finalize a combatant's turn and emit post-action updates."""

    active_id, legacy_active_id = canonical_entity_pair(actor)

    await push_progress_update(
        context.progress,
        context.combat_party.members,
        context.foes,
        context.enrage_state,
        context.temp_rdr,
        _EXTRA_TURNS,
        context.turn,
        run_id=context.run_id,
        active_id=active_id,
        legacy_active_id=legacy_active_id,
        active_target_id=active_target_id,
        legacy_active_target_id=legacy_active_target_id,
        include_summon_foes=include_summon_foes,
        visual_queue=context.visual_queue,
        turn_phase="resolve",
    )
    await push_progress_update(
        context.progress,
        context.combat_party.members,
        context.foes,
        context.enrage_state,
        context.temp_rdr,
        _EXTRA_TURNS,
        context.turn,
        run_id=context.run_id,
        active_id=active_id,
        legacy_active_id=legacy_active_id,
        active_target_id=active_target_id,
        legacy_active_target_id=legacy_active_target_id,
        include_summon_foes=include_summon_foes,
        visual_queue=context.visual_queue,
        turn_phase="end",
    )
    await _pace(action_start)
    cycle_count = await dispatch_turn_end_snapshot(
        context.visual_queue,
        context.progress,
        context.combat_party.members,
        context.foes,
        context.enrage_state,
        context.temp_rdr,
        _EXTRA_TURNS,
        actor,
        context.turn,
        context.run_id,
        turn_phase="turn_end",
        spent_override=spent_override,
    )
    if cycle_count:
        context.turn += cycle_count
    # ``pace_sleep`` multiplies the provided value by ``TURN_PACING`` internally.
    await pace_sleep(2.2)
    await pace_sleep(YIELD_MULTIPLIER)
