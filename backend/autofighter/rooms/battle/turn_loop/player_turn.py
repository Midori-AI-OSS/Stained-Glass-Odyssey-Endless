from __future__ import annotations

import asyncio
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
from ..turn_helpers import remove_dead_foes
from ..turns import apply_enrage_bleed
from ..turns import mutate_snapshot_overlay
from ..turns import push_progress_update
from ..turns import register_snapshot_entities
from ..turns import update_enrage_state
from .initialization import TurnLoopContext
from .turn_end import finish_turn

log = logging.getLogger("autofighter.rooms.battle.turn_loop")


async def execute_player_phase(context: TurnLoopContext) -> bool:
    """Process all player-controlled turns and report whether battle continues."""

    for member in context.combat_party.members:
        member_effect = member.effect_manager
        if member.action_points <= 0:
            member.action_points = member.actions_per_turn
            for _ in range(max(0, member.action_points - 1)):
                try:
                    await BUS.emit_async("extra_turn", member)
                except Exception:
                    pass
        safety = 0
        while True:
            safety += 1
            if safety > 10:
                break
            action_start = asyncio.get_event_loop().time()
            if member.hp <= 0:
                await pace_sleep(YIELD_MULTIPLIER)
                break
            context.turn += 1
            enrage_update = await update_enrage_state(
                context.turn,
                context.enrage_state,
                context.foes,
                context.foe_effects,
                context.enrage_mods,
                context.combat_party.members,
            )
            if enrage_update:
                await push_progress_update(
                    context.progress,
                    context.combat_party.members,
                    context.foes,
                    context.enrage_state,
                    context.temp_rdr,
                    _EXTRA_TURNS,
                    run_id=context.run_id,
                    active_id=getattr(member, "id", None),
                    active_target_id=None,
                )
                await pace_sleep(YIELD_MULTIPLIER)
            await context.registry.trigger("turn_start", member)
            if context.run_id is not None:
                await _abort_other_runs(context, context.run_id)
            await context.registry.trigger_turn_start(
                member,
                turn=context.turn,
                party=context.combat_party.members,
                foes=context.foes,
                enrage_active=context.enrage_state.active,
            )
            await BUS.emit_async("turn_start", member)
            log.debug("%s turn start", member.id)
            await member.maybe_regain(context.turn)
            if not _any_foes_alive(context.foes):
                break
            alive_targets = [
                (index, foe_obj)
                for index, foe_obj in enumerate(context.foes)
                if foe_obj.hp > 0
            ]
            if not alive_targets:
                break
            target_index, target_foe = _select_target(alive_targets)
            await BUS.emit_async("target_acquired", member, target_foe)
            mutate_snapshot_overlay(
                context.run_id,
                active_id=getattr(member, "id", None),
                active_target_id=getattr(target_foe, "id", None),
            )
            await pace_sleep(YIELD_MULTIPLIER)
            target_manager = context.foe_effects[target_index]
            damage_type = getattr(member, "damage_type", None)
            await member_effect.tick(target_manager)
            for foe_obj in context.foes:
                context.exp_reward, context.temp_rdr = await credit_if_dead(
                    foe_obj=foe_obj,
                    exp_reward=context.exp_reward,
                    temp_rdr=context.temp_rdr,
                    **context.credit_kwargs,
                )
            remove_dead_foes(
                foes=context.foes,
                foe_effects=context.foe_effects,
                enrage_mods=context.enrage_mods,
            )
            if not context.foes:
                break
            if member.hp <= 0:
                await context.registry.trigger(
                    "turn_end",
                    member,
                    party=context.combat_party.members,
                    foes=context.foes,
                )
                await pace_sleep(YIELD_MULTIPLIER)
                break
            proceed = await member_effect.on_action()
            if proceed is None:
                proceed = True
            if proceed and hasattr(damage_type, "on_action"):
                result = await damage_type.on_action(
                    member,
                    context.combat_party.members,
                    context.foes,
                )
                proceed = True if result is None else bool(result)
            await _handle_ultimate(context, member, damage_type)
            if not proceed:
                await BUS.emit_async("action_used", member, member, 0)
                await context.registry.trigger(
                    "turn_end",
                    member,
                    party=context.combat_party.members,
                    foes=context.foes,
                )
                if (
                    _EXTRA_TURNS.get(id(member), 0) > 0
                    and member.hp > 0
                ):
                    _EXTRA_TURNS[id(member)] -= 1
                    await _pace(action_start)
                    continue
                await push_progress_update(
                    context.progress,
                    context.combat_party.members,
                    context.foes,
                    context.enrage_state,
                    context.temp_rdr,
                    _EXTRA_TURNS,
                    run_id=context.run_id,
                    active_id=member.id,
                    active_target_id=getattr(target_foe, "id", None),
                    include_summon_foes=True,
                )
                await _pace(action_start)
                await pace_sleep(YIELD_MULTIPLIER)
                break
            damage = await target_foe.apply_damage(
                member.atk,
                attacker=member,
                action_name="Normal Attack",
            )
            if damage <= 0:
                queue_log(
                    "%s's attack was dodged by %s",
                    member.id,
                    target_foe.id,
                )
            else:
                queue_log(
                    "%s hits %s for %s",
                    member.id,
                    target_foe.id,
                    damage,
                )
                damage_type_id = (
                    getattr(member.damage_type, "id", "generic")
                    if hasattr(member, "damage_type")
                    else "generic"
                )
                await BUS.emit_async(
                    "hit_landed",
                    member,
                    target_foe,
                    damage,
                    "attack",
                    f"{damage_type_id}_attack",
                )
                await context.registry.trigger_hit_landed(
                    member,
                    target_foe,
                    damage,
                    "attack",
                    damage_type=damage_type_id,
                    party=context.combat_party.members,
                    foes=context.foes,
                )
            target_manager.maybe_inflict_dot(member, damage)
            targets_hit = 1
            if getattr(member.damage_type, "id", "").lower() == "wind":
                targets_hit += await _handle_wind_spread(
                    context,
                    member,
                    target_index,
                )
            await BUS.emit_async("action_used", member, target_foe, damage)
            duration = calc_animation_time(member, targets_hit)
            if duration > 0:
                await BUS.emit_async(
                    "animation_start",
                    member,
                    targets_hit,
                    duration,
                )
                try:
                    await asyncio.sleep(duration)
                finally:
                    await BUS.emit_async(
                        "animation_end",
                        member,
                        targets_hit,
                        duration,
                    )
            await impact_pause(member, targets_hit, duration=duration)
            await context.registry.trigger(
                "action_taken",
                member,
                target=target_foe,
                damage=damage,
                party=context.combat_party.members,
                foes=context.foes,
            )
            try:
                party_summons_added = SummonManager.add_summons_to_party(
                    context.combat_party
                )
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
                        active_id=getattr(member, "id", None),
                        active_target_id=getattr(target_foe, "id", None),
                        include_summon_foes=True,
                    )
                    await pace_sleep(YIELD_MULTIPLIER)
            except Exception:
                pass
            member.add_ultimate_charge(member.actions_per_turn)
            for ally in context.combat_party.members:
                ally.handle_ally_action(member)
            await apply_enrage_bleed(
                context.enrage_state,
                context.combat_party.members,
                context.foes,
                context.foe_effects,
            )
            context.exp_reward, context.temp_rdr = await credit_if_dead(
                foe_obj=target_foe,
                exp_reward=context.exp_reward,
                temp_rdr=context.temp_rdr,
                **context.credit_kwargs,
            )
            remove_dead_foes(
                foes=context.foes,
                foe_effects=context.foe_effects,
                enrage_mods=context.enrage_mods,
            )
            battle_over = not context.foes
            await context.registry.trigger(
                "turn_end",
                member,
                party=context.combat_party.members,
                foes=context.foes,
            )
            await context.registry.trigger_turn_end(member)
            member.action_points = max(0, member.action_points - 1)
            if (
                _EXTRA_TURNS.get(id(member), 0) > 0
                and member.hp > 0
                and not battle_over
            ):
                _EXTRA_TURNS[id(member)] -= 1
                await _pace(action_start)
                await pace_sleep(YIELD_MULTIPLIER)
                continue
            await finish_turn(
                context,
                member,
                action_start,
                active_target_id=getattr(target_foe, "id", None),
            )
            if battle_over:
                break
            break
        if not context.foes:
            break
    if not context.foes:
        return False
    if not any(member.hp > 0 for member in context.combat_party.members):
        return False
    return True


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


def _any_foes_alive(foes: list[Any]) -> bool:
    return any(getattr(foe_obj, "hp", 0) > 0 for foe_obj in foes)


def _select_target(alive_targets: list[tuple[int, Any]]) -> tuple[int, Any]:
    weights = [max(getattr(foe_obj, "aggro", 0.0), 0.0) for _, foe_obj in alive_targets]
    if sum(weights) > 0:
        return random.choices(alive_targets, weights=weights)[0]
    return random.choice(alive_targets)


async def _handle_ultimate(
    context: TurnLoopContext,
    member: Any,
    damage_type: Any,
) -> None:
    if not (
        getattr(member, "ultimate_ready", False)
        and hasattr(damage_type, "ultimate")
    ):
        return

    ultimate_type = getattr(getattr(member, "damage_type", None), "id", "generic")
    try:
        await BUS.emit_async(
            "ultimate_used",
            member,
            None,
            0,
            "ultimate",
            {"ultimate_type": ultimate_type},
        )
        await damage_type.ultimate(
            member,
            context.combat_party.members,
            context.foes,
        )
        await BUS.emit_async(
            "ultimate_completed",
            member,
            None,
            0,
            "ultimate",
            {"ultimate_type": ultimate_type},
        )
    except Exception as exc:
        await BUS.emit_async(
            "ultimate_failed",
            member,
            None,
            0,
            "ultimate",
            {"ultimate_type": ultimate_type, "error": str(exc)},
        )


async def _handle_wind_spread(
    context: TurnLoopContext,
    member: Any,
    target_index: int,
) -> int:
    try:
        living_targets = sum(
            1 for foe_obj in context.foes if getattr(foe_obj, "hp", 0) > 0
        )
    except Exception:
        living_targets = len(context.foes) if isinstance(context.foes, list) else 1
    living_targets = max(1, int(living_targets))
    scale = 1.0 / (2.0 * living_targets)
    scaled_atk = member.atk * scale
    additional_hits = 0
    for extra_index, extra_foe in enumerate(context.foes):
        if extra_index == target_index or extra_foe.hp <= 0:
            await pace_sleep(YIELD_MULTIPLIER)
            continue
        extra_damage = await extra_foe.apply_damage(
            scaled_atk,
            attacker=member,
            action_name="Wind Spread",
        )
        additional_hits += 1
        if extra_damage <= 0:
            queue_log(
                "%s's attack was dodged by %s",
                member.id,
                extra_foe.id,
            )
        else:
            queue_log(
                "%s hits %s for %s",
                member.id,
                extra_foe.id,
                extra_damage,
            )
            await BUS.emit_async(
                "hit_landed",
                member,
                extra_foe,
                extra_damage,
                "attack",
                "wind_multi_attack",
            )
            await context.registry.trigger_hit_landed(
                member,
                extra_foe,
                extra_damage,
                "wind_multi_attack",
                damage_type="wind",
                party=context.combat_party.members,
                foes=context.foes,
            )
        context.foe_effects[extra_index].maybe_inflict_dot(member, extra_damage)
        context.exp_reward, context.temp_rdr = await credit_if_dead(
            foe_obj=extra_foe,
            exp_reward=context.exp_reward,
            temp_rdr=context.temp_rdr,
            **context.credit_kwargs,
        )
        remove_dead_foes(
            foes=context.foes,
            foe_effects=context.foe_effects,
            enrage_mods=context.enrage_mods,
        )
        if not context.foes:
            break
    return additional_hits
