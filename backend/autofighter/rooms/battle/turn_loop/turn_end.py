from __future__ import annotations

from typing import Any

from ..pacing import _EXTRA_TURNS
from ..pacing import TURN_PACING
from ..pacing import YIELD_MULTIPLIER
from ..pacing import _pace
from ..pacing import pace_sleep
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
) -> None:
    """Finalize a combatant's turn and emit post-action updates."""

    await push_progress_update(
        context.progress,
        context.combat_party.members,
        context.foes,
        context.enrage_state,
        context.temp_rdr,
        _EXTRA_TURNS,
        context.turn,
        run_id=context.run_id,
        active_id=getattr(actor, "id", None),
        active_target_id=active_target_id,
        include_summon_foes=include_summon_foes,
        visual_queue=context.visual_queue,
        turn_phase="resolve",
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
        turn_phase="end",
    )
    if cycle_count:
        context.turn += cycle_count
    await pace_sleep(2.2 * TURN_PACING)
    await pace_sleep(YIELD_MULTIPLIER)
