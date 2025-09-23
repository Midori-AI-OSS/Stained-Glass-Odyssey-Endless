from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING
from typing import Any
from typing import Awaitable
from typing import Callable
from typing import MutableMapping
from typing import Sequence

from autofighter.effects import DamageOverTime
from autofighter.effects import create_stat_buff

from ...stats import Stats
from ...stats import set_enrage_percent
from . import snapshots as _snapshots
from . import enrage as _enrage
from .events import register_event_handlers
from .progress import build_battle_progress_payload

if TYPE_CHECKING:
    from autofighter.effects import EffectManager

log = logging.getLogger(__name__)


register_snapshot_entities = _snapshots.register_snapshot_entities
prepare_snapshot_overlay = _snapshots.prepare_snapshot_overlay
mutate_snapshot_overlay = _snapshots.mutate_snapshot_overlay

register_event_handlers()

async def push_progress_update(
    progress: Callable[[dict[str, Any]], Awaitable[None]] | None,
    party_members: Sequence[Stats],
    foes: Sequence[Stats],
    enrage_state: EnrageState,
    rdr: float,
    extra_turns: MutableMapping[int, int],
    turn: int,
    *,
    run_id: str | None,
    active_id: str | None,
    active_target_id: str | None = None,
    include_summon_foes: bool = False,
    ended: bool | None = None,
) -> None:
    """Send a progress update if a callback is available."""

    if progress is None:
        return
    payload = await build_battle_progress_payload(
        party_members,
        foes,
        enrage_state,
        rdr,
        extra_turns,
        turn,
        run_id=run_id,
        active_id=active_id,
        active_target_id=active_target_id,
        include_summon_foes=include_summon_foes,
        ended=ended,
    )
    await progress(payload)


async def _advance_visual_queue(
    visual_queue: Any,
    actor: Stats | None,
) -> None:
    if visual_queue is None or actor is None:
        return
    try:
        await asyncio.to_thread(visual_queue.advance_with_actor, actor)
    except Exception:
        log.debug("Failed to advance visual queue", exc_info=True)


async def dispatch_turn_end_snapshot(
    visual_queue: Any,
    progress: Callable[[dict[str, Any]], Awaitable[None]] | None,
    party_members: Sequence[Stats],
    foes: Sequence[Stats],
    enrage_state: EnrageState,
    rdr: float,
    extra_turns: MutableMapping[int, int],
    actor: Stats,
    turn: int,
    run_id: str | None,
) -> None:
    """Advance the visual queue and emit an updated snapshot."""

    await _advance_visual_queue(visual_queue, actor)
    await push_progress_update(
        progress,
        party_members,
        foes,
        enrage_state,
        rdr,
        extra_turns,
        turn,
        run_id=run_id,
        active_id=getattr(actor, "id", None),
        active_target_id=None,
    )


EnrageState = _enrage.EnrageState


async def update_enrage_state(
    turn: int,
    state: EnrageState,
    foes: Sequence[Stats],
    foe_effects: Sequence["EffectManager"],
    enrage_mods: list[Any],
    party_members: Sequence[Stats],
) -> dict[str, Any] | None:
    """Delegate enrage updates to the helper module."""

    return await _enrage.update_enrage_state(
        turn,
        state,
        foes,
        foe_effects,
        enrage_mods,
        party_members,
        set_enrage_percent=set_enrage_percent,
        create_stat_buff=create_stat_buff,
    )


async def apply_enrage_bleed(
    state: EnrageState,
    party_members: Sequence[Stats],
    foes: Sequence[Stats],
    foe_effects: Sequence["EffectManager"],
) -> None:
    """Delegate bleed application to the helper module."""

    await _enrage.apply_enrage_bleed(
        state,
        party_members,
        foes,
        foe_effects,
        damage_over_time_factory=DamageOverTime,
    )
