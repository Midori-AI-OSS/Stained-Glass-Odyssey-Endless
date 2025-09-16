from __future__ import annotations

import asyncio
from collections.abc import Awaitable
from collections.abc import Callable
import logging
import random
from typing import TYPE_CHECKING
from typing import Any

from autofighter.effects import EffectManager
from autofighter.stats import BUS
from autofighter.stats import calc_animation_time
from autofighter.summons.manager import SummonManager

from .logging import queue_log
from .pacing import _EXTRA_TURNS
from .pacing import _pace
from .turns import EnrageState
from .turns import apply_enrage_bleed
from .turns import dispatch_turn_end_snapshot
from .turns import push_progress_update
from .turns import update_enrage_state

if TYPE_CHECKING:
    from ...party import Party
    from .core import BattleRoom


log = logging.getLogger(__name__)


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
    battle_tasks: dict[str, asyncio.Task[Any]],
    abort: Callable[[str], None],
) -> tuple[int, float, int]:
    """Execute the asynchronous turn processing loop."""

    credited_foe_ids: set[str] = set()

    async def _credit_if_dead(foe_obj: Any) -> None:
        nonlocal exp_reward, temp_rdr
        try:
            foe_id = getattr(foe_obj, "id", None)
            if getattr(foe_obj, "hp", 1) <= 0 and foe_id and foe_id not in credited_foe_ids:
                await BUS.emit_async(
                    "entity_killed",
                    foe_obj,
                    None,
                    0,
                    "death",
                    {"victim_type": "foe", "killer_type": "party"},
                )
                exp_reward += foe_obj.level * 12 + 5 * room.node.index
                temp_rdr += 0.55
                credited_foe_ids.add(foe_id)
                try:
                    label = (
                        getattr(foe_obj, "name", None)
                        or getattr(foe_obj, "id", "")
                    ).lower()
                    if "slime" in label:
                        for member in combat_party.members:
                            member.exp_multiplier += 0.025
                        for member in party.members:
                            member.exp_multiplier += 0.025
                except Exception:
                    pass
        except Exception:
            pass

    def _remove_dead_foes() -> None:
        for index in range(len(foes) - 1, -1, -1):
            if getattr(foes[index], "hp", 1) <= 0:
                foes.pop(index)
                foe_effects.pop(index)
                enrage_mods.pop(index)

    turn = 0

    for entity in list(combat_party.members) + list(foes):
        entity.action_points = entity.actions_per_turn
        for _ in range(max(0, entity.action_points - 1)):
            try:
                await BUS.emit_async("extra_turn", entity)
            except Exception:
                pass

    if progress is not None:
        await push_progress_update(
            progress,
            combat_party.members,
            foes,
            enrage_state,
            temp_rdr,
            _EXTRA_TURNS,
            active_id=None,
            include_summon_foes=True,
        )
        try:
            await asyncio.sleep(3)
        except Exception:
            pass

    while any(foe_obj.hp > 0 for foe_obj in foes) and any(
        member.hp > 0 for member in combat_party.members
    ):
        for member in combat_party.members:
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
                    await asyncio.sleep(0.001)
                    break
                turn += 1
                await update_enrage_state(
                    turn,
                    enrage_state,
                    foes,
                    foe_effects,
                    enrage_mods,
                    combat_party.members,
                )
                await registry.trigger("turn_start", member)
                if run_id is not None:
                    for other_id, task in list(battle_tasks.items()):
                        if other_id != run_id and not task.done():
                            other_task = battle_tasks.pop(other_id, None)
                            current_task = battle_tasks.pop(run_id, None)
                            if other_task:
                                other_task.cancel()
                            if current_task and not current_task.done():
                                current_task.cancel()
                            abort(other_id)
                await registry.trigger_turn_start(
                    member,
                    turn=turn,
                    party=combat_party.members,
                    foes=foes,
                    enrage_active=enrage_state.active,
                )
                await BUS.emit_async("turn_start", member)
                log.debug("%s turn start", member.id)
                await member.maybe_regain(turn)
                if not any(foe_obj.hp > 0 for foe_obj in foes):
                    break
                alive_targets = [
                    (index, foe_obj)
                    for index, foe_obj in enumerate(foes)
                    if foe_obj.hp > 0
                ]
                if not alive_targets:
                    break
                weights = [max(foe_obj.aggro, 0.0) for _, foe_obj in alive_targets]
                if sum(weights) > 0:
                    target_index, target_foe = random.choices(
                        alive_targets,
                        weights=weights,
                    )[0]
                else:
                    target_index, target_foe = random.choice(alive_targets)
                target_manager = foe_effects[target_index]
                damage_type = getattr(member, "damage_type", None)
                await member_effect.tick(target_manager)
                for foe_obj in foes:
                    await _credit_if_dead(foe_obj)
                _remove_dead_foes()
                if not foes:
                    break
                if member.hp <= 0:
                    await registry.trigger(
                        "turn_end",
                        member,
                        party=combat_party.members,
                        foes=foes,
                    )
                    await asyncio.sleep(0.001)
                    break
                proceed = await member_effect.on_action()
                if proceed is None:
                    proceed = True
                if proceed and hasattr(damage_type, "on_action"):
                    result = await damage_type.on_action(
                        member,
                        combat_party.members,
                        foes,
                    )
                    proceed = True if result is None else bool(result)
                if getattr(member, "ultimate_ready", False) and hasattr(
                    damage_type,
                    "ultimate",
                ):
                    try:
                        await BUS.emit_async(
                            "ultimate_used",
                            member,
                            None,
                            0,
                            "ultimate",
                            {
                                "ultimate_type": getattr(
                                    member.damage_type,
                                    "id",
                                    "generic",
                                )
                            },
                        )
                        await damage_type.ultimate(
                            member,
                            combat_party.members,
                            foes,
                        )
                        await BUS.emit_async(
                            "ultimate_completed",
                            member,
                            None,
                            0,
                            "ultimate",
                            {
                                "ultimate_type": getattr(
                                    member.damage_type,
                                    "id",
                                    "generic",
                                )
                            },
                        )
                    except Exception as exc:
                        await BUS.emit_async(
                            "ultimate_failed",
                            member,
                            None,
                            0,
                            "ultimate",
                            {
                                "ultimate_type": getattr(
                                    member.damage_type,
                                    "id",
                                    "generic",
                                ),
                                "error": str(exc),
                            },
                        )
                if not proceed:
                    await BUS.emit_async("action_used", member, member, 0)
                    await registry.trigger(
                        "turn_end",
                        member,
                        party=combat_party.members,
                        foes=foes,
                    )
                    if _EXTRA_TURNS.get(id(member), 0) > 0 and member.hp > 0:
                        _EXTRA_TURNS[id(member)] -= 1
                        await _pace(action_start)
                        continue
                    await push_progress_update(
                        progress,
                        combat_party.members,
                        foes,
                        enrage_state,
                        temp_rdr,
                        _EXTRA_TURNS,
                        active_id=member.id,
                        include_summon_foes=True,
                    )
                    await _pace(action_start)
                    await asyncio.sleep(0.001)
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
                    await registry.trigger_hit_landed(
                        member,
                        target_foe,
                        damage,
                        "attack",
                        damage_type=damage_type_id,
                        party=combat_party.members,
                        foes=foes,
                    )
                target_manager.maybe_inflict_dot(member, damage)
                targets_hit = 1
                if getattr(member.damage_type, "id", "").lower() == "wind":
                    try:
                        living_targets = sum(
                            1 for foe_obj in foes if getattr(foe_obj, "hp", 0) > 0
                        )
                    except Exception:
                        living_targets = len(foes) if isinstance(foes, list) else 1
                    living_targets = max(1, int(living_targets))
                    scale = 1.0 / (2.0 * living_targets)
                    scaled_atk = member.atk * scale
                    for extra_index, extra_foe in enumerate(foes):
                        if extra_index == target_index or extra_foe.hp <= 0:
                            await asyncio.sleep(0.001)
                            continue
                        extra_damage = await extra_foe.apply_damage(
                            scaled_atk,
                            attacker=member,
                            action_name="Wind Spread",
                        )
                        targets_hit += 1
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
                            await registry.trigger_hit_landed(
                                member,
                                extra_foe,
                                extra_damage,
                                "wind_multi_attack",
                                damage_type="wind",
                                party=combat_party.members,
                                foes=foes,
                            )
                        foe_effects[extra_index].maybe_inflict_dot(member, extra_damage)
                        await _credit_if_dead(extra_foe)
                        _remove_dead_foes()
                        if not foes:
                            break
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
                await registry.trigger(
                    "action_taken",
                    member,
                    target=target_foe,
                    damage=damage,
                    party=combat_party.members,
                    foes=foes,
                )
                try:
                    SummonManager.add_summons_to_party(combat_party)
                    for owner in list(foes):
                        owner_id = getattr(owner, "id", str(id(owner)))
                        for summon in SummonManager.get_summons(owner_id):
                            if summon not in foes:
                                foes.append(summon)
                                manager = EffectManager(summon)
                                summon.effect_manager = manager
                                foe_effects.append(manager)
                                enrage_mods.append(None)
                except Exception:
                    pass
                member.add_ultimate_charge(member.actions_per_turn)
                for ally in combat_party.members:
                    ally.handle_ally_action(member)
                await apply_enrage_bleed(
                    enrage_state,
                    combat_party.members,
                    foes,
                    foe_effects,
                )
                await _credit_if_dead(target_foe)
                _remove_dead_foes()
                battle_over = not foes
                await registry.trigger(
                    "turn_end",
                    member,
                    party=combat_party.members,
                    foes=foes,
                )
                await registry.trigger_turn_end(member)
                member.action_points = max(0, member.action_points - 1)
                if (
                    _EXTRA_TURNS.get(id(member), 0) > 0
                    and member.hp > 0
                    and not battle_over
                ):
                    _EXTRA_TURNS[id(member)] -= 1
                    await _pace(action_start)
                    await asyncio.sleep(0.001)
                    continue
                await push_progress_update(
                    progress,
                    combat_party.members,
                    foes,
                    enrage_state,
                    temp_rdr,
                    _EXTRA_TURNS,
                    active_id=member.id,
                )
                await _pace(action_start)
                await dispatch_turn_end_snapshot(
                    visual_queue,
                    progress,
                    combat_party.members,
                    foes,
                    enrage_state,
                    temp_rdr,
                    _EXTRA_TURNS,
                    member,
                )
                await asyncio.sleep(2.2)
                await asyncio.sleep(0.001)
                if battle_over:
                    break
                break
        if not foes:
            break
        if not any(member.hp > 0 for member in combat_party.members):
            break
        for foe_index, acting_foe in enumerate(list(foes)):
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
                action_start = asyncio.get_event_loop().time()
                if acting_foe.hp <= 0:
                    await asyncio.sleep(0.001)
                    break
                alive_targets = [
                    (index, target)
                    for index, target in enumerate(combat_party.members)
                    if target.hp > 0
                ]
                if not alive_targets:
                    break
                weights = [max(target.aggro, 0.0) for _, target in alive_targets]
                if sum(weights) > 0:
                    player_index, target = random.choices(
                        alive_targets,
                        weights=weights,
                    )[0]
                else:
                    player_index, target = random.choice(alive_targets)
                target_effect = target.effect_manager
                foe_manager = foe_effects[foe_index]
                await registry.trigger("turn_start", acting_foe)
                if run_id is not None:
                    for other_id, task in list(battle_tasks.items()):
                        if other_id != run_id and not task.done():
                            other_task = battle_tasks.pop(other_id, None)
                            current_task = battle_tasks.pop(run_id, None)
                            if other_task:
                                other_task.cancel()
                            if current_task and not current_task.done():
                                current_task.cancel()
                            abort(other_id)
                await BUS.emit_async("turn_start", acting_foe)
                log.debug(
                    "%s turn start targeting %s",
                    acting_foe.id,
                    target.id,
                )
                await acting_foe.maybe_regain(turn)
                damage_type = getattr(acting_foe, "damage_type", None)
                await foe_manager.tick(target_effect)
                for foe_obj in foes:
                    await _credit_if_dead(foe_obj)
                if all(foe_obj.hp <= 0 for foe_obj in foes):
                    break
                if acting_foe.hp <= 0:
                    await registry.trigger(
                        "turn_end",
                        acting_foe,
                        party=combat_party.members,
                        foes=foes,
                    )
                    await asyncio.sleep(0.001)
                    break
                proceed = await foe_manager.on_action()
                if proceed is None:
                    proceed = True
                if proceed and hasattr(damage_type, "on_action"):
                    result = await damage_type.on_action(
                        acting_foe,
                        foes,
                        combat_party.members,
                    )
                    proceed = True if result is None else bool(result)
                if getattr(acting_foe, "ultimate_ready", False) and hasattr(
                    damage_type,
                    "ultimate",
                ):
                    try:
                        await BUS.emit_async(
                            "ultimate_used",
                            acting_foe,
                            None,
                            0,
                            "ultimate",
                            {
                                "ultimate_type": getattr(
                                    acting_foe.damage_type,
                                    "id",
                                    "generic",
                                ),
                                "caster_type": "foe",
                            },
                        )
                        await damage_type.ultimate(
                            acting_foe,
                            foes,
                            combat_party.members,
                        )
                        await BUS.emit_async(
                            "ultimate_completed",
                            acting_foe,
                            None,
                            0,
                            "ultimate",
                            {
                                "ultimate_type": getattr(
                                    acting_foe.damage_type,
                                    "id",
                                    "generic",
                                ),
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
                                "ultimate_type": getattr(
                                    acting_foe.damage_type,
                                    "id",
                                    "generic",
                                ),
                                "caster_type": "foe",
                                "error": str(exc),
                            },
                        )
                if not proceed:
                    await BUS.emit_async(
                        "action_used",
                        acting_foe,
                        acting_foe,
                        0,
                    )
                    acting_foe.add_ultimate_charge(acting_foe.actions_per_turn)
                    battle_over = not any(
                        member.hp > 0 for member in combat_party.members
                    )
                    await registry.trigger(
                        "turn_end",
                        acting_foe,
                        party=combat_party.members,
                        foes=foes,
                    )
                    if (
                        _EXTRA_TURNS.get(id(acting_foe), 0) > 0
                        and acting_foe.hp > 0
                        and not battle_over
                    ):
                        _EXTRA_TURNS[id(acting_foe)] -= 1
                        await _pace(action_start)
                        continue
                    await push_progress_update(
                        progress,
                        combat_party.members,
                        foes,
                        enrage_state,
                        temp_rdr,
                        _EXTRA_TURNS,
                        active_id=acting_foe.id,
                    )
                    await _pace(action_start)
                    await dispatch_turn_end_snapshot(
                        visual_queue,
                        progress,
                        combat_party.members,
                        foes,
                        enrage_state,
                        temp_rdr,
                        _EXTRA_TURNS,
                        acting_foe,
                    )
                    await asyncio.sleep(2.2)
                    await asyncio.sleep(0.001)
                    break
                damage = await target.apply_damage(acting_foe.atk, attacker=acting_foe)
                if damage <= 0:
                    queue_log(
                        "%s's attack was dodged by %s",
                        acting_foe.id,
                        target.id,
                    )
                else:
                    queue_log(
                        "%s hits %s for %s",
                        acting_foe.id,
                        target.id,
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
                await registry.trigger("action_taken", acting_foe)
                try:
                    SummonManager.add_summons_to_party(combat_party)
                    for owner in list(foes):
                        owner_id = getattr(owner, "id", str(id(owner)))
                        for summon in SummonManager.get_summons(owner_id):
                            if summon not in foes:
                                foes.append(summon)
                                manager = EffectManager(summon)
                                summon.effect_manager = manager
                                foe_effects.append(manager)
                                enrage_mods.append(None)
                except Exception:
                    pass
                acting_foe.add_ultimate_charge(acting_foe.actions_per_turn)
                for ally in foes:
                    ally.handle_ally_action(acting_foe)
                battle_over = not any(member.hp > 0 for member in combat_party.members)
                await registry.trigger(
                    "turn_end",
                    acting_foe,
                    party=combat_party.members,
                    foes=foes,
                )
                await registry.trigger_turn_end(acting_foe)
                acting_foe.action_points = max(0, acting_foe.action_points - 1)
                if (
                    _EXTRA_TURNS.get(id(acting_foe), 0) > 0
                    and acting_foe.hp > 0
                    and not battle_over
                ):
                    _EXTRA_TURNS[id(acting_foe)] -= 1
                    await _pace(action_start)
                    await asyncio.sleep(0.001)
                    continue
                await push_progress_update(
                    progress,
                    combat_party.members,
                    foes,
                    enrage_state,
                    temp_rdr,
                    _EXTRA_TURNS,
                    active_id=acting_foe.id,
                )
                await _pace(action_start)
                await dispatch_turn_end_snapshot(
                    visual_queue,
                    progress,
                    combat_party.members,
                    foes,
                    enrage_state,
                    temp_rdr,
                    _EXTRA_TURNS,
                    acting_foe,
                )
                await asyncio.sleep(2.2)
                await asyncio.sleep(0.001)
                if battle_over:
                    break
                break
        _remove_dead_foes()
        if not foes:
            break

    return turn, temp_rdr, exp_reward
