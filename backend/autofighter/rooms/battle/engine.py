"""Async battle engine handling turn processing and rewards."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable
from collections.abc import Callable
import logging
import random
from typing import Any
from typing import TYPE_CHECKING

from battle_logging.writers import end_battle_logging
from services.user_level_service import gain_user_exp
from services.user_level_service import get_user_level

from autofighter.cards import card_choices
from autofighter.effects import EffectManager
from autofighter.relics import relic_choices
from autofighter.stats import BUS
from autofighter.stats import Stats
from autofighter.stats import calc_animation_time
from autofighter.stats import set_enrage_percent
from autofighter.summons.base import Summon
from autofighter.summons.manager import SummonManager
from plugins.damage_types import ALL_DAMAGE_TYPES

from ...party import Party
from .logging import queue_log
from .pacing import _EXTRA_TURNS
from .pacing import _pace
from .rewards import _apply_rdr_to_stars
from .rewards import _calc_gold
from .rewards import _pick_card_stars
from .rewards import _pick_item_stars
from .rewards import _pick_relic_stars
from .rewards import _roll_relic_drop
from .setup import BattleSetupResult
from .turns import EnrageState
from .turns import apply_enrage_bleed
from .turns import build_action_queue_snapshot
from .turns import collect_summon_snapshots
from .turns import dispatch_turn_end_snapshot
from .turns import push_progress_update
from .turns import update_enrage_state

if TYPE_CHECKING:
    from .core import BattleRoom


log = logging.getLogger(__name__)


ELEMENTS = [e.lower() for e in ALL_DAMAGE_TYPES]


async def run_battle(
    room: BattleRoom,
    *,
    party: Party,
    setup_data: BattleSetupResult,
    start_gold: int,
    enrage_threshold: int,
    progress: Callable[[dict[str, Any]], Awaitable[None]] | None = None,
    run_id: str | None = None,
    battle_snapshots: dict[str, dict[str, Any]] | None = None,
    battle_tasks: dict[str, asyncio.Task[Any]] | None = None,
) -> dict[str, Any]:
    """Execute the main battle loop and return the resolution payload."""

    registry = setup_data.registry
    combat_party = setup_data.combat_party
    foes = setup_data.foes
    foe_effects = setup_data.foe_effects
    enrage_mods = setup_data.enrage_mods
    visual_queue = setup_data.visual_queue
    battle_logger = setup_data.battle_logger

    battle_snapshots = battle_snapshots or {}
    battle_tasks = battle_tasks or {}

    for foe_obj in foes:
        await BUS.emit_async("battle_start", foe_obj)
        await registry.trigger(
            "battle_start",
            foe_obj,
            party=combat_party.members,
            foes=foes,
        )

    log.info(
        "Battle start: %s vs %s",
        [f.id for f in foes],
        [m.id for m in combat_party.members],
    )

    for member in combat_party.members:
        await BUS.emit_async("battle_start", member)
        await registry.trigger(
            "battle_start",
            member,
            party=combat_party.members,
            foes=foes,
        )

    enrage_state = EnrageState(threshold=enrage_threshold)
    set_enrage_percent(0.0)

    exp_reward = 0
    credited_foe_ids: set[str] = set()

    def _abort(other_id: str) -> None:
        msg = "concurrent battle detected"
        snap = {
            "result": "error",
            "error": msg,
            "ended": True,
            "party": [],
            "foes": [],
            "awaiting_next": False,
            "awaiting_card": False,
            "awaiting_relic": False,
            "awaiting_loot": False,
        }
        if run_id is not None:
            battle_snapshots[run_id] = snap
        battle_snapshots[other_id] = snap
        raise RuntimeError(msg)

    temp_rdr = party.rdr

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
                            _abort(other_id)
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
                            _abort(other_id)
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

    if progress is not None:
        try:
            await push_progress_update(
                progress,
                combat_party.members,
                foes,
                enrage_state,
                temp_rdr,
                _EXTRA_TURNS,
                active_id=None,
                ended=True,
            )
        except Exception:
            pass

    try:
        for foe_obj in foes:
            if getattr(foe_obj, "hp", 1) <= 0:
                await BUS.emit_async("entity_defeat", foe_obj)
        for member in combat_party.members:
            if getattr(member, "hp", 1) <= 0:
                await BUS.emit_async("entity_defeat", member)
    except Exception:
        pass

    try:
        for foe_obj in foes:
            await BUS.emit_async("battle_end", foe_obj)
    except Exception:
        pass

    battle_result = (
        "defeat"
        if all(member.hp <= 0 for member in combat_party.members)
        else "victory"
    )
    end_battle_logging(battle_result)

    party.members = combat_party.members
    party.gold = combat_party.gold
    party.relics = combat_party.relics
    party.cards = combat_party.cards

    if any(member.hp > 0 for member in party.members) and exp_reward > 0:
        for member in party.members:
            try:
                member.gain_exp(exp_reward)
            except Exception:
                pass
        try:
            level = get_user_level()
            await gain_user_exp(int(exp_reward / max(1, level)))
        except Exception:
            pass

    foes_data = await asyncio.to_thread(
        lambda: [_serialize(foe_obj) for foe_obj in foes]
    )

    def _apply_display_overrides(payload: dict[str, Any]) -> None:
        stacks_for_display = payload.get("stacks", 0) if payload.get("active") else 0
        for foe_obj, foe_info in zip(foes, foes_data, strict=False):
            if isinstance(foe_obj, Summon):
                continue
            try:
                base_atk = foe_obj.get_base_stat("atk")
            except Exception:
                base_atk = getattr(foe_obj, "atk", 0)
            display_base = int(round(base_atk / 20)) if base_atk else 0
            foe_info["atk"] = display_base + stacks_for_display * 2

    for mod in enrage_mods:
        if mod is not None:
            mod.remove()
    for member in combat_party.members:
        manager = member.effect_manager
        await manager.cleanup(member)
    for foe_obj, manager in zip(foes, foe_effects, strict=False):
        await manager.cleanup(foe_obj)

    try:
        set_enrage_percent(0.0)
    except Exception:
        pass

    try:
        from autofighter.stats import set_battle_active

        set_battle_active(False)
    except Exception:
        pass

    party_data = await asyncio.to_thread(
        lambda: [_serialize(member) for member in party.members]
    )
    party_summons, foe_summons = await asyncio.gather(
        collect_summon_snapshots(party.members),
        collect_summon_snapshots(foes),
    )
    action_queue_snapshot = await build_action_queue_snapshot(
        party.members,
        foes,
        _EXTRA_TURNS,
    )
    SummonManager.cleanup()

    if all(member.hp <= 0 for member in combat_party.members):
        loot = {
            "gold": 0,
            "card_choices": [],
            "relic_choices": [],
            "items": [],
        }
        enrage_payload = enrage_state.as_payload()
        if enrage_payload.get("active"):
            stacks_display = max(turn - enrage_threshold, 0)
            enrage_payload["stacks"] = stacks_display
            enrage_payload["turns"] = stacks_display
        _apply_display_overrides(enrage_payload)

        return {
            "result": "defeat",
            "party": party_data,
            "party_summons": party_summons,
            "gold": party.gold,
            "relics": party.relics,
            "cards": party.cards,
            "card_choices": [],
            "relic_choices": [],
            "loot": loot,
            "foes": [
                foe_info
                for foe_obj, foe_info in zip(foes, foes_data, strict=False)
                if not isinstance(foe_obj, Summon)
            ],
            "foe_summons": foe_summons,
            "room_number": room.node.index,
            "exp_reward": exp_reward,
            "enrage": enrage_payload,
            "rdr": temp_rdr,
            "action_queue": action_queue_snapshot,
            "ended": True,
        }

    selected_cards: list[Any] = []
    attempts = 0
    log.info(
        "Starting card selection for run %s, party has %d cards",
        getattr(combat_party, "cards", []),
        len(getattr(combat_party, "cards", [])),
    )
    while len(selected_cards) < 3 and attempts < 30:
        attempts += 1
        base_stars = _pick_card_stars(room)
        card_stars = _apply_rdr_to_stars(base_stars, temp_rdr)
        log.debug(
            "Card selection attempt %d: base_stars=%d, rdr_stars=%d",
            attempts,
            base_stars,
            card_stars,
        )
        choices = card_choices(combat_party, card_stars, count=1)
        log.debug("  card_choices returned %d options", len(choices))
        if not choices:
            log.debug("  No cards available for star level %d", card_stars)
            continue
        candidate = choices[0]
        log.debug(
            "  Candidate card: %s (%s) - %d stars",
            candidate.id,
            candidate.name,
            candidate.stars,
        )
        if any(card.id == candidate.id for card in selected_cards):
            log.debug("  Card %s already selected, skipping", candidate.id)
            continue
        selected_cards.append(candidate)
        log.debug("  Added card: %s", candidate.id)
    log.info(
        "Card selection complete: %d cards selected after %d attempts",
        len(selected_cards),
        attempts,
    )
    if selected_cards:
        log.info("Selected cards: %s", [card.id for card in selected_cards])
    else:
        log.warning("No cards were selected!")
    card_choice_data = [
        {
            "id": card.id,
            "name": card.name,
            "stars": card.stars,
            "about": card.about,
        }
        for card in selected_cards
    ]

    relic_options: list[Any] = []
    if _roll_relic_drop(room, temp_rdr):
        picked: list[Any] = []
        tries = 0
        while len(picked) < 3 and tries < 30:
            tries += 1
            relic_stars = _apply_rdr_to_stars(
                _pick_relic_stars(room),
                temp_rdr,
            )
            choices = relic_choices(combat_party, relic_stars, count=1)
            if not choices:
                continue
            relic = choices[0]
            if any(existing.id == relic.id for existing in picked):
                continue
            picked.append(relic)
        relic_options = picked

    if not selected_cards:
        from plugins.relics.fallback_essence import FallbackEssence

        fallback_relic = FallbackEssence()
        if not relic_options:
            relic_options = [fallback_relic]
        else:
            relic_options.append(fallback_relic)

    relic_choice_data = [
        {
            "id": relic.id,
            "name": relic.name,
            "stars": relic.stars,
            "about": relic.describe(party.relics.count(relic.id) + 1),
            "stacks": party.relics.count(relic.id),
        }
        for relic in relic_options
    ]

    gold_reward = _calc_gold(room, temp_rdr)
    party.gold += gold_reward
    await BUS.emit_async("gold_earned", gold_reward)

    item_base = 1 * temp_rdr
    base_int = int(item_base)
    item_count = max(1, base_int)
    if random.random() < item_base - base_int:
        item_count += 1
    items = [
        {"id": random.choice(ELEMENTS), "stars": _pick_item_stars(room)}
        for _ in range(item_count)
    ]
    ticket_chance = 0.0005 * temp_rdr
    if random.random() < ticket_chance:
        items.append({"id": "ticket", "stars": 0})

    loot = {
        "gold": party.gold - start_gold,
        "card_choices": card_choice_data,
        "relic_choices": relic_choice_data,
        "items": items,
    }
    log.info(
        "Battle rewards: gold=%s cards=%s relics=%s items=%s",
        loot["gold"],
        [choice["id"] for choice in card_choice_data],
        [choice["id"] for choice in relic_choice_data],
        items,
    )

    enrage_payload = enrage_state.as_payload()
    if enrage_payload.get("active"):
        stacks_display = max(turn - enrage_threshold, 0)
        enrage_payload["stacks"] = stacks_display
        enrage_payload["turns"] = stacks_display
    _apply_display_overrides(enrage_payload)

    return {
        "result": "boss" if room.strength > 1.0 else "battle",
        "party": party_data,
        "party_summons": party_summons,
        "gold": party.gold,
        "relics": party.relics,
        "cards": party.cards,
        "card_choices": card_choice_data,
        "relic_choices": relic_choice_data,
        "loot": loot,
        "foes": [
            foe_info
            for foe_obj, foe_info in zip(foes, foes_data, strict=False)
            if not isinstance(foe_obj, Summon)
        ],
        "foe_summons": foe_summons,
        "room_number": room.node.index,
        "battle_index": getattr(battle_logger, "battle_index", 0) if battle_logger else 0,
        "exp_reward": exp_reward,
        "enrage": enrage_payload,
        "rdr": party.rdr,
        "action_queue": action_queue_snapshot,
        "ended": True,
    }


from ..utils import _serialize  # noqa: E402  # imported late to avoid cycles

