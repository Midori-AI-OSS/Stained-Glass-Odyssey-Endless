from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from typing import Any
from typing import Awaitable
from typing import Callable

from .cleanup import battle_active
from .cleanup import cleanup_after_round
from .foe_turn import execute_foe_phase
from .initialization import initialize_turn_loop
from .player_turn import execute_player_phase

if TYPE_CHECKING:
    from asyncio import Task

    from autofighter.effects import EffectManager

    from ...party import Party
    from ..core import BattleRoom
    from ..turns import EnrageState


log = logging.getLogger("autofighter.rooms.battle.turn_loop")


async def run_turn_loop(
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
) -> tuple[int, float, int]:
    """Execute the asynchronous turn processing loop."""

    context = await initialize_turn_loop(
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
    )

    from .timeouts import TurnTimeoutError as _TurnTimeoutError

    while battle_active(context):
        try:
            player_continues = await execute_player_phase(context)
        except _TurnTimeoutError as exc:
            try:
                log.exception("Player phase timed out", exc_info=exc)
            except Exception:
                pass
            raise
        if not player_continues:
            break
        try:
            foe_continues = await execute_foe_phase(context)
        except _TurnTimeoutError as exc:
            try:
                log.exception("Foe phase timed out", exc_info=exc)
            except Exception:
                pass
            raise
        still_active = cleanup_after_round(context)
        if not foe_continues or not still_active:
            break

    return context.turn, context.temp_rdr, context.exp_reward
