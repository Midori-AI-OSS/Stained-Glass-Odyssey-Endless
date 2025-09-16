from __future__ import annotations

import asyncio
from typing import Any

from ..pacing import _EXTRA_TURNS
from ..pacing import _pace
from ..turns import dispatch_turn_end_snapshot
from ..turns import push_progress_update
from .initialization import TurnLoopContext


async def finish_turn(
    context: TurnLoopContext,
    actor: Any,
    action_start: float,
    *,
    include_summon_foes: bool = False,
) -> None:
    """Finalize a combatant's turn and emit post-action updates."""

    await push_progress_update(
        context.progress,
        context.combat_party.members,
        context.foes,
        context.enrage_state,
        context.temp_rdr,
        _EXTRA_TURNS,
        active_id=getattr(actor, "id", None),
        include_summon_foes=include_summon_foes,
    )
    await _pace(action_start)
    await dispatch_turn_end_snapshot(
        context.visual_queue,
        context.progress,
        context.combat_party.members,
        context.foes,
        context.enrage_state,
        context.temp_rdr,
        _EXTRA_TURNS,
        actor,
    )
    await asyncio.sleep(2.2)
    await asyncio.sleep(0.001)
