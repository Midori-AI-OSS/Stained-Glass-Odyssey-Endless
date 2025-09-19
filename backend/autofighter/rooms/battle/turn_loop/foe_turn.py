from __future__ import annotations

import asyncio
from contextlib import suppress
from dataclasses import dataclass
import logging
import random
from typing import Any

from autofighter.effects import EffectManager
from autofighter.stats import BUS
from autofighter.stats import calc_animation_time
from autofighter.summons.manager import SummonManager

from ..logging import queue_log
from ..pacing import _EXTRA_TURNS
from ..pacing import YIELD_MULTIPLIER
from ..pacing import _pace
from ..pacing import impact_pause
from ..pacing import pace_sleep
from ..turn_helpers import credit_if_dead
from ..turns import mutate_snapshot_overlay
from ..turns import push_progress_update
from ..turns import register_snapshot_entities
from .initialization import TurnLoopContext
from .timeouts import TURN_TIMEOUT_SECONDS
from .timeouts import TurnTimeoutError
from .timeouts import identify_actor
from .timeouts import write_timeout_log
from .turn_end import finish_turn

log = logging.getLogger("autofighter.rooms.battle.turn_loop")


@dataclass(slots=True)
class FoeTurnIterationResult:
    repeat: bool
    battle_over: bool


async def execute_foe_phase(context: TurnLoopContext) -> bool:
    """Execute all foe-controlled turns and report whether the battle continues."""

    for foe_index, acting_foe in enumerate(list(context.foes)):
        if acting_foe.action_points <= 0:
            acting_foe.action_points = acting_foe.actions_per_turn
            for _ in range(max(0, acting_foe.action_points - 1)):
                try:
                    await BUS.emit_async("extra_turn", acting_foe)
                except Exception:
                    pass
        safety = 0
        while True:
            safety += 1
            if safety > 10:
                break
            iteration = asyncio.create_task(
                _run_foe_turn_iteration(context, foe_index, acting_foe)
            )
            try:
                result = await asyncio.wait_for(iteration, TURN_TIMEOUT_SECONDS)
            except asyncio.TimeoutError as exc:
                iteration.cancel()
                with suppress(Exception):
                    await asyncio.gather(iteration, return_exceptions=True)
                actor_id = identify_actor(acting_foe)
                timeout_path = await write_timeout_log(
                    actor=acting_foe,
                    role="foe",
                    turn=context.turn,
                    run_id=context.run_id,
                )
                try:
                    log.error(
                        "Foe turn timed out for %s; details saved to %s",
                        actor_id,
                        timeout_path,
                    )
                except Exception:
                    pass
                raise TurnTimeoutError(actor_id, str(timeout_path)) from exc
            if result.battle_over or not any(
                member.hp > 0 for member in context.combat_party.members
            ):
                break
            if not result.repeat:
                break
        if not context.foes or not any(
            member.hp > 0 for member in context.combat_party.members
        ):
            break
    if not context.foes:
        return False
    if not any(member.hp > 0 for member in context.combat_party.members):
        return False
    return True


async def _run_foe_turn_iteration(
    context: TurnLoopContext,
    foe_index: int,
    acting_foe: Any,
) -> FoeTurnIterationResult:
    action_start = asyncio.get_event_loop().time()
    if acting_foe.hp <= 0:
        await pace_sleep(YIELD_MULTIPLIER)
        return FoeTurnIterationResult(repeat=False, battle_over=False)

    alive_targets = [
        (index, target)
        for index, target in enumerate(context.combat_party.members)
        if getattr(target, "hp", 0) > 0
    ]
    if not alive_targets:
        return FoeTurnIterationResult(repeat=False, battle_over=True)

    _, target = _select_target(alive_targets)
    await BUS.emit_async("target_acquired", acting_foe, target)
    mutate_snapshot_overlay(
        context.run_id,
        active_id=getattr(acting_foe, "id", None),
        active_target_id=getattr(target, "id", None),
    )
    await pace_sleep(YIELD_MULTIPLIER)

    target_effect = target.effect_manager
    foe_manager = context.foe_effects[foe_index]
    await context.registry.trigger("turn_start", acting_foe)
    if context.run_id is not None:
        await _abort_other_runs(context, context.run_id)
    await BUS.emit_async("turn_start", acting_foe)
    log.debug(
        "%s turn start targeting %s",
        getattr(acting_foe, "id", acting_foe),
        getattr(target, "id", target),
    )
    await acting_foe.maybe_regain(context.turn)

    damage_type = getattr(acting_foe, "damage_type", None)
    await foe_manager.tick(target_effect)
    for foe_obj in context.foes:
        context.exp_reward, context.temp_rdr = await credit_if_dead(
            foe_obj=foe_obj,
            exp_reward=context.exp_reward,
            temp_rdr=context.temp_rdr,
            **context.credit_kwargs,
        )

    if all(getattr(foe_obj, "hp", 0) <= 0 for foe_obj in context.foes):
        return FoeTurnIterationResult(repeat=False, battle_over=True)

    if acting_foe.hp <= 0:
        await context.registry.trigger(
            "turn_end",
            acting_foe,
            party=context.combat_party.members,
            foes=context.foes,
        )
        await pace_sleep(YIELD_MULTIPLIER)
        return FoeTurnIterationResult(repeat=False, battle_over=False)

    proceed = await foe_manager.on_action()
    if proceed is None:
        proceed = True
    if proceed and hasattr(damage_type, "on_action"):
        result = await damage_type.on_action(
            acting_foe,
            context.foes,
            context.combat_party.members,
        )
        proceed = True if result is None else bool(result)

    await _handle_ultimate(context, acting_foe, damage_type)

    if not proceed:
        await BUS.emit_async("action_used", acting_foe, acting_foe, 0)
        acting_foe.add_ultimate_charge(acting_foe.actions_per_turn)
        battle_over = not any(
            member.hp > 0 for member in context.combat_party.members
        )
        await context.registry.trigger(
            "turn_end",
            acting_foe,
            party=context.combat_party.members,
            foes=context.foes,
        )
        if (
            _EXTRA_TURNS.get(id(acting_foe), 0) > 0
            and acting_foe.hp > 0
            and not battle_over
        ):
            _EXTRA_TURNS[id(acting_foe)] -= 1
            await _pace(action_start)
            return FoeTurnIterationResult(repeat=True, battle_over=False)

        await finish_turn(
            context,
            acting_foe,
            action_start,
            active_target_id=getattr(target, "id", None),
        )
        return FoeTurnIterationResult(repeat=False, battle_over=battle_over)

    damage = await target.apply_damage(acting_foe.atk, attacker=acting_foe)
    if damage <= 0:
        queue_log(
            "%s's attack was dodged by %s",
            getattr(acting_foe, "id", acting_foe),
            getattr(target, "id", target),
        )
    else:
        queue_log(
            "%s hits %s for %s",
            getattr(acting_foe, "id", acting_foe),
            getattr(target, "id", target),
            damage,
        )
        damage_type_id = (
            getattr(acting_foe.damage_type, "id", "generic")
            if hasattr(acting_foe, "damage_type")
            else "generic"
        )
        await BUS.emit_async(
            "hit_landed",
            acting_foe,
            target,
            damage,
            "attack",
            f"foe_{damage_type_id}_attack",
        )

    target_effect.maybe_inflict_dot(acting_foe, damage)
    targets_hit = 1
    await BUS.emit_async("action_used", acting_foe, target, damage)
    duration = calc_animation_time(acting_foe, targets_hit)
    if duration > 0:
        await BUS.emit_async(
            "animation_start",
            acting_foe,
            targets_hit,
            duration,
        )
        try:
            await asyncio.sleep(duration)
        finally:
            await BUS.emit_async(
                "animation_end",
                acting_foe,
                targets_hit,
                duration,
            )

    await impact_pause(acting_foe, targets_hit, duration=duration)
    await context.registry.trigger("action_taken", acting_foe)

    try:
        party_summons_added = SummonManager.add_summons_to_party(context.combat_party)
        register_snapshot_entities(
            context.run_id,
            context.combat_party.members,
        )
        new_foe_summons: list[Any] = []
        for owner in list(context.foes):
            owner_id = getattr(owner, "id", str(id(owner)))
            for summon in SummonManager.get_summons(owner_id):
                if summon not in context.foes:
                    context.foes.append(summon)
                    manager: EffectManager = EffectManager(summon)
                    summon.effect_manager = manager
                    context.foe_effects.append(manager)
                    context.enrage_mods.append(None)
                    register_snapshot_entities(context.run_id, [summon])
                    new_foe_summons.append(summon)
        if party_summons_added or new_foe_summons:
            await push_progress_update(
                context.progress,
                context.combat_party.members,
                context.foes,
                context.enrage_state,
                context.temp_rdr,
                _EXTRA_TURNS,
                run_id=context.run_id,
                active_id=getattr(acting_foe, "id", None),
                active_target_id=getattr(target, "id", None),
                include_summon_foes=True,
            )
            await pace_sleep(YIELD_MULTIPLIER)
    except Exception:
        pass

    acting_foe.add_ultimate_charge(acting_foe.actions_per_turn)
    for ally in context.foes:
        ally.handle_ally_action(acting_foe)

    battle_over = not any(member.hp > 0 for member in context.combat_party.members)
    await context.registry.trigger(
        "turn_end",
        acting_foe,
        party=context.combat_party.members,
        foes=context.foes,
    )
    await context.registry.trigger_turn_end(acting_foe)

    acting_foe.action_points = max(0, acting_foe.action_points - 1)
    if (
        _EXTRA_TURNS.get(id(acting_foe), 0) > 0
        and acting_foe.hp > 0
        and not battle_over
    ):
        _EXTRA_TURNS[id(acting_foe)] -= 1
        await _pace(action_start)
        await pace_sleep(YIELD_MULTIPLIER)
        return FoeTurnIterationResult(repeat=True, battle_over=False)

    await finish_turn(
        context,
        acting_foe,
        action_start,
        active_target_id=getattr(target, "id", None),
    )

    return FoeTurnIterationResult(repeat=False, battle_over=battle_over)


async def _abort_other_runs(context: TurnLoopContext, run_id: str) -> None:
    for other_id, task in list(context.battle_tasks.items()):
        if other_id != run_id and not task.done():
            other_task = context.battle_tasks.pop(other_id, None)
            current_task = context.battle_tasks.pop(run_id, None)
            if other_task:
                other_task.cancel()
            if current_task and not current_task.done():
                current_task.cancel()
            context.abort(other_id)


def _select_target(alive_targets: list[tuple[int, Any]]) -> tuple[int, Any]:
    weights = [max(getattr(target, "aggro", 0.0), 0.0) for _, target in alive_targets]
    if sum(weights) > 0:
        return random.choices(alive_targets, weights=weights)[0]
    return random.choice(alive_targets)


async def _handle_ultimate(
    context: TurnLoopContext,
    acting_foe: Any,
    damage_type: Any,
) -> None:
    if not (
        getattr(acting_foe, "ultimate_ready", False)
        and hasattr(damage_type, "ultimate")
    ):
        return

    ultimate_type = getattr(getattr(acting_foe, "damage_type", None), "id", "generic")
    try:
        await BUS.emit_async(
            "ultimate_used",
            acting_foe,
            None,
            0,
            "ultimate",
            {
                "ultimate_type": ultimate_type,
                "caster_type": "foe",
            },
        )
        await damage_type.ultimate(
            acting_foe,
            context.foes,
            context.combat_party.members,
        )
        await BUS.emit_async(
            "ultimate_completed",
            acting_foe,
            None,
            0,
            "ultimate",
            {
                "ultimate_type": ultimate_type,
                "caster_type": "foe",
            },
        )
    except Exception as exc:
        await BUS.emit_async(
            "ultimate_failed",
            acting_foe,
            None,
            0,
            "ultimate",
            {
                "ultimate_type": ultimate_type,
                "caster_type": "foe",
                "error": str(exc),
            },
        )
