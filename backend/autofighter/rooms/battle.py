from __future__ import annotations

import asyncio
from collections.abc import Awaitable
from collections.abc import Callable
import copy
from dataclasses import dataclass
import logging
import random
from typing import Any

from battle_logging import end_battle_logging

# Import battle logging
from battle_logging import start_battle_logging
from services.user_level_service import gain_user_exp
from services.user_level_service import get_user_level

from autofighter.cards import apply_cards
from autofighter.cards import card_choices
from autofighter.effects import EffectManager
from autofighter.effects import StatModifier
from autofighter.effects import create_stat_buff
from autofighter.mapgen import MapNode
from autofighter.relics import apply_relics
from autofighter.relics import relic_choices
from autofighter.summons.base import Summon
from autofighter.summons.manager import SummonManager
from plugins.damage_types import ALL_DAMAGE_TYPES

from ..action_queue import ActionQueue
from ..party import Party
from ..passives import PassiveRegistry
from ..stats import BUS
from ..stats import Stats
from ..stats import calc_animation_time
from ..stats import set_enrage_percent
from . import Room
from .utils import _build_foes
from .utils import _scale_stats
from .utils import _serialize

log = logging.getLogger(__name__)

ENRAGE_TURNS_NORMAL = 100
ENRAGE_TURNS_BOSS = 500

# Explicit pacing between combat actions (seconds)
TURN_PACING = 0.5

_EXTRA_TURNS: dict[int, int] = {}
_VISUAL_QUEUE: ActionQueue | None = None


def _grant_extra_turn(entity: Stats) -> None:
    ident = id(entity)
    _EXTRA_TURNS[ident] = _EXTRA_TURNS.get(ident, 0) + 1
    try:
        if _VISUAL_QUEUE is not None:
            _VISUAL_QUEUE.grant_extra_turn(entity)
    except Exception:
        pass


def _clear_extra_turns(_entity: Stats) -> None:
    _EXTRA_TURNS.clear()
    global _VISUAL_QUEUE
    _VISUAL_QUEUE = None


BUS.subscribe("extra_turn", _grant_extra_turn)
BUS.subscribe("battle_end", _clear_extra_turns)

ELEMENTS = [e.lower() for e in ALL_DAMAGE_TYPES]


def _pick_card_stars(room: Room) -> int:
    """Determine the star rank for card rewards."""
    roll = random.random()
    if isinstance(room, BossRoom):
        if roll < 0.60:
            return 3
        if roll < 0.85:
            return 4
        return 5
    if isinstance(room, BattleRoom) and room.strength > 1.0:
        if roll < 0.40:
            return 1
        if roll < 0.70:
            return 2
        if roll < 0.7015:
            return 3
        if roll < 0.7025:
            return 4
        return 5
    return 1 if roll < 0.80 else 2


def _roll_relic_drop(room: Room, rdr: float) -> bool:
    """Check whether a relic drops based on room type and RDR."""
    roll = random.random()
    base = 0.5 if isinstance(room, BossRoom) else 0.1
    return roll < min(base * rdr, 1.0)


def _pick_item_stars(room: Room) -> int:
    """Select upgrade item star rank based on room difficulty."""
    node = room.node
    if node.room_type == "battle-boss-floor":
        low, high = 3, 4
    elif isinstance(room, BossRoom) or getattr(room, "strength", 1.0) > 1.0:
        low, high = 1, 3
    else:
        low, high = 1, 2
    base = low + (node.floor - 1) // 20 + (node.loop - 1) + node.pressure // 10
    return min(base, high)


def _calc_gold(room: Room, rdr: float) -> int:
    """Calculate gold reward for the room."""
    node = room.node
    if node.room_type == "battle-boss-floor":
        base = 200
        mult = random.uniform(2.05, 4.25)
    elif isinstance(room, BossRoom) or getattr(room, "strength", 1.0) > 1.0:
        base = 20
        mult = random.uniform(1.53, 2.25)
    else:
        base = 5
        mult = random.uniform(1.01, 1.25)
    return int(base * node.loop * mult * rdr)


def _pick_relic_stars(room: Room) -> int:
    roll = random.random()
    if isinstance(room, BossRoom):
        if roll < 0.6:
            return 3
        if roll < 0.9:
            return 4
        return 5
    if roll < 0.7:
        return 1
    if roll < 0.9:
        return 2
    return 3


def _apply_rdr_to_stars(stars: int, rdr: float) -> int:
    """Chance to upgrade stars with extreme `rdr` values."""
    for threshold in (10.0, 10000.0):
        if stars >= 5 or rdr < threshold:
            break
        chance = min(rdr / (threshold * 10.0), 0.99)
        if random.random() < chance:
            stars += 1
        else:
            break
    return stars


@dataclass
class BattleRoom(Room):
    """Standard battle room where the party fights a group of foes."""

    node: MapNode
    strength: float = 1.0

    async def resolve(
        self,
        party: Party,
        data: dict[str, Any],
        progress: Callable[[dict[str, Any]], Awaitable[None]] | None = None,
        foe: Stats | list[Stats] | None = None,
        run_id: str | None = None,
    ) -> dict[str, Any]:
        from game import battle_snapshots
        from game import battle_tasks

        registry = PassiveRegistry()
        start_gold = party.gold
        if foe is None:
            foes = _build_foes(self.node, party)
        else:
            foes = foe if isinstance(foe, list) else [foe]
        for f in foes:
            _scale_stats(f, self.node, self.strength)
        foe = foes[0]
        combat_party = Party(
            members=[copy.deepcopy(m) for m in party.members],
            gold=party.gold,
            relics=party.relics,
            cards=party.cards,
            rdr=party.rdr,
        )
        await apply_cards(combat_party)
        apply_relics(combat_party)
        party.rdr = combat_party.rdr

        foe_effects = []
        for f in foes:
            mgr = EffectManager(f)
            f.effect_manager = mgr
            foe_effects.append(mgr)
        enrage_mods: list[StatModifier | None] = [None for _ in foes]

        party_effects = []
        # Mark battle as active to allow damage/heal processing
        try:
            from autofighter.stats import set_battle_active
            set_battle_active(True)
        except Exception:
            pass
        for member in combat_party.members:
            mgr = EffectManager(member)
            member.effect_manager = mgr
            party_effects.append(mgr)

        # Initialize a visual action queue for UI snapshots (mid-left action bar)
        try:
            q_entities = [
                e for e in list(combat_party.members) + list(foes)
                if not isinstance(e, Summon)
            ]
            _visual_queue = ActionQueue(q_entities)
        except Exception:
            _visual_queue = None
        global _VISUAL_QUEUE
        _VISUAL_QUEUE = _visual_queue

        # Start battle logging once before emitting any events so participants are captured
        battle_logger = start_battle_logging()
        try:
            if battle_logger is not None:
                battle_logger.summary.party_members = [m.id for m in combat_party.members]
                battle_logger.summary.foes = [f.id for f in foes]
                # Snapshot party relics present at battle start (id -> count)
                relic_counts: dict[str, int] = {}
                for rid in combat_party.relics:
                    relic_counts[rid] = relic_counts.get(rid, 0) + 1
                battle_logger.summary.party_relics = relic_counts
        except Exception:
            pass

        for f in foes:
            await BUS.emit_async("battle_start", f)
            await registry.trigger("battle_start", f, party=combat_party.members, foes=foes)

        log.info(
            "Battle start: %s vs %s",
            [f.id for f in foes],
            [m.id for m in combat_party.members],
        )
        for member_effect, member in zip(party_effects, combat_party.members, strict=False):
            await BUS.emit_async("battle_start", member)
            await registry.trigger("battle_start", member, party=combat_party.members, foes=foes)

        enrage_active = False
        enrage_stacks = 0
        enrage_bleed_applies = 0
        # Ensure enrage percent starts at 0 for this battle
        set_enrage_percent(0.0)
        threshold = ENRAGE_TURNS_BOSS if isinstance(self, BossRoom) else ENRAGE_TURNS_NORMAL
        exp_reward = 0
        credited_foe_ids: set[str] = set()

        def _collect_summons(
            entities: list[Stats],
        ) -> dict[str, list[dict[str, Any]]]:
            snapshots: dict[str, list[dict[str, Any]]] = {}
            for ent in entities:
                sid = getattr(ent, "id", str(id(ent)))
                for summon in SummonManager.get_summons(sid):
                    snap = _serialize(summon)
                    snap["owner_id"] = sid
                    snapshots.setdefault(sid, []).append(snap)
            return snapshots

        def _queue_snapshot() -> list[dict[str, Any]]:
            ordered = sorted(
                [
                    c
                    for c in combat_party.members + foes
                    if not isinstance(c, Summon)
                ],
                key=lambda c: getattr(c, "action_value", 0.0),
            )
            extras: list[dict[str, Any]] = []
            for ent in ordered:
                turns = _EXTRA_TURNS.get(id(ent), 0)
                for _ in range(turns):
                    extras.append(
                        {
                            "id": getattr(ent, "id", ""),
                            "action_gauge": getattr(ent, "action_gauge", 0),
                            "action_value": getattr(ent, "action_value", 0.0),
                            "base_action_value": getattr(ent, "base_action_value", 0.0),
                            "bonus": True,
                        }
                    )
            return extras + [
                {
                    "id": getattr(c, "id", ""),
                    "action_gauge": getattr(c, "action_gauge", 0),
                    "action_value": getattr(c, "action_value", 0.0),
                    "base_action_value": getattr(c, "base_action_value", 0.0),
                }
                for c in ordered
            ]

        def _advance_queue(actor: Stats) -> None:
            """Advance the visual action queue using the provided actor."""
            try:
                if _visual_queue is None:
                    return
                _visual_queue.advance_with_actor(actor)
            except Exception:
                pass

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

        async def _credit_if_dead(foe_obj) -> None:
            nonlocal exp_reward, temp_rdr
            try:
                fid = getattr(foe_obj, "id", None)
                if getattr(foe_obj, "hp", 1) <= 0 and fid and fid not in credited_foe_ids:
                    # Emit kill event - async for better performance
                    await BUS.emit_async("entity_killed", foe_obj, None, 0, "death", {"victim_type": "foe", "killer_type": "party"})

                    exp_reward += foe_obj.level * 12 + 5 * self.node.index
                    temp_rdr += 0.55
                    credited_foe_ids.add(fid)
                    try:
                        label = (getattr(foe_obj, "name", None) or getattr(foe_obj, "id", "")).lower()
                        if "slime" in label:
                            for m in combat_party.members:
                                m.exp_multiplier += 0.025
                            for m in party.members:
                                m.exp_multiplier += 0.025
                    except Exception:
                        pass
            except Exception:
                # Never let EXP crediting break battle flow
                pass

        def _remove_dead_foes() -> None:
            for i in range(len(foes) - 1, -1, -1):
                if getattr(foes[i], "hp", 1) <= 0:
                    foes.pop(i)
                    foe_effects.pop(i)
                    enrage_mods.pop(i)
        turn = 0
        temp_rdr = party.rdr

        # Initialize action points and queue extras before the first snapshot
        for ent in list(combat_party.members) + list(foes):
            ent.action_points = ent.actions_per_turn
            for _ in range(max(0, ent.action_points - 1)):
                try:
                    BUS.emit("extra_turn", ent)
                except Exception:
                    pass
        if progress is not None:
            await progress(
                {
                    "result": "battle",
                    "party": [
                        _serialize(m)
                        for m in combat_party.members
                        if not isinstance(m, Summon)
                    ],
                    "foes": [_serialize(f) for f in foes],
                    "party_summons": _collect_summons(combat_party.members),
                    "foe_summons": _collect_summons(foes),
                    "enrage": {"active": False, "stacks": 0, "turns": 0},
                    "rdr": temp_rdr,
                    "action_queue": _queue_snapshot(),
                    "active_id": None,
                }
            )
            try:
                await asyncio.sleep(3)
            except Exception:
                pass
        # Helper to pace actions: dynamic pacing based on combatant count
        async def _pace(start_time: float) -> None:
            try:
                elapsed = asyncio.get_event_loop().time() - start_time
            except Exception:
                elapsed = 0.0

            # Enforce a half-second delay after each action for pacing
            base_wait = TURN_PACING
            wait = base_wait - elapsed
            if wait > 0:
                try:
                    await asyncio.sleep(wait)
                except Exception:
                    pass

            # Always pause an additional half-second between turns
            try:
                await asyncio.sleep(TURN_PACING)
            except Exception:
                pass

        while any(f.hp > 0 for f in foes) and any(
            m.hp > 0 for m in combat_party.members
        ):
            for member_effect, member in zip(party_effects, combat_party.members, strict=False):
                if member.action_points <= 0:
                    member.action_points = member.actions_per_turn
                    for _ in range(max(0, member.action_points - 1)):
                        try:
                            BUS.emit("extra_turn", member)
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
                    if turn > threshold:
                        if not enrage_active:
                            enrage_active = True
                            for f in foes:
                                f.passives.append("Enraged")
                            log.info("Enrage activated")
                        new_stacks = turn - threshold
                        # Make enrage much stronger: each stack adds +135% damage taken
                        # and massive damage dealt bonuses.
                        set_enrage_percent(1.35 * max(new_stacks, 0))
                        mult = 1 + 2.0 * new_stacks
                        for i, (f, mgr) in enumerate(zip(foes, foe_effects, strict=False)):
                            if enrage_mods[i] is not None:
                                enrage_mods[i].remove()
                                try:
                                    mgr.mods.remove(enrage_mods[i])
                                    if enrage_mods[i].id in f.mods:
                                        f.mods.remove(enrage_mods[i].id)
                                except ValueError:
                                    pass
                            mod = create_stat_buff(f, name="enrage_atk", atk_mult=mult, turns=9999)
                            mgr.add_modifier(mod)
                            enrage_mods[i] = mod
                        enrage_stacks = new_stacks
                        if turn > 1000:
                            turns_in_enrage = max(enrage_stacks, 0)
                            extra_damage = 100 * turns_in_enrage
                            for m in combat_party.members:
                                if m.hp > 0 and extra_damage > 0:
                                    await m.apply_damage(extra_damage)
                            for f in foes:
                                if f.hp > 0 and extra_damage > 0:
                                    await f.apply_damage(extra_damage)
                    else:
                        # Not enraged yet; ensure percent is zero
                        set_enrage_percent(0.0)
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
                    # Also trigger the enhanced turn_start method with battle context
                    await registry.trigger_turn_start(member, turn=turn, party=combat_party.members, foes=foes, enrage_active=enrage_active)
                    # Emit BUS event for relics that subscribe to turn_start - async for better performance
                    await BUS.emit_async("turn_start", member)
                    log.debug("%s turn start", member.id)
                    await member.maybe_regain(turn)
                    # If all foes died earlier in this round, stop taking actions
                    if not any(f.hp > 0 for f in foes):
                        break
                    alive_targets = [
                        (i, f) for i, f in enumerate(foes) if f.hp > 0
                    ]
                    if not alive_targets:
                        break
                    weights = [max(f.aggro, 0.0) for _, f in alive_targets]
                    if sum(weights) > 0:
                        tgt_idx, tgt_foe = random.choices(
                            alive_targets, weights=weights
                        )[0]
                    else:
                        tgt_idx, tgt_foe = random.choice(alive_targets)
                    tgt_mgr = foe_effects[tgt_idx]
                    dt = getattr(member, "damage_type", None)
                    await member_effect.tick(tgt_mgr)
                    # Credit any foes that died due to DoT/HoT ticks
                    for f in foes:
                        await _credit_if_dead(f)
                    _remove_dead_foes()
                    if not foes:
                        break
                    if member.hp <= 0:
                        await registry.trigger("turn_end", member, party=combat_party.members, foes=foes)
                        await asyncio.sleep(0.001)
                        break
                    proceed = await member_effect.on_action()
                    if proceed is None:
                        proceed = True
                    if proceed and hasattr(dt, "on_action"):
                        res = await dt.on_action(
                            member,
                            combat_party.members,
                            foes,
                        )
                        proceed = True if res is None else bool(res)
                    if getattr(member, "ultimate_ready", False) and hasattr(dt, "ultimate"):
                        if hasattr(member, "use_ultimate") and member.use_ultimate():
                            try:
                                # Emit ultimate start event
                                await BUS.emit_async("ultimate_used", member, None, 0, "ultimate", {"ultimate_type": getattr(member.damage_type, 'id', 'generic')})
                                await dt.ultimate(member, combat_party.members, foes)
                                # Emit ultimate end event
                                await BUS.emit_async("ultimate_completed", member, None, 0, "ultimate", {"ultimate_type": getattr(member.damage_type, 'id', 'generic')})
                            except Exception as e:
                                # Emit ultimate failed event
                                await BUS.emit_async("ultimate_failed", member, None, 0, "ultimate", {"ultimate_type": getattr(member.damage_type, 'id', 'generic'), "error": str(e)})
                                pass
                    if not proceed:
                        await BUS.emit_async("action_used", member, member, 0)
                        await registry.trigger("turn_end", member, party=combat_party.members, foes=foes)
                        if _EXTRA_TURNS.get(id(member), 0) > 0 and member.hp > 0:
                            _EXTRA_TURNS[id(member)] -= 1
                            await _pace(action_start)
                            continue
                        if progress is not None:
                            await progress(
                                {
                                    "result": "battle",
                                    "party": [
                                        _serialize(m)
                                        for m in combat_party.members
                                        if not isinstance(m, Summon)
                                    ],
                                    "foes": [_serialize(f) for f in foes],
                                    "party_summons": _collect_summons(combat_party.members),
                                    "foe_summons": _collect_summons(foes),
                                    "enrage": {
                                        "active": enrage_active,
                                        "stacks": enrage_stacks,
                                        "turns": enrage_stacks,
                                    },
                                    "rdr": temp_rdr,
                                    "action_queue": _queue_snapshot(),
                                    "active_id": member.id,
                                }
                            )
                        await _pace(action_start)
                        await asyncio.sleep(0.001)
                        break
                    dmg = await tgt_foe.apply_damage(member.atk, attacker=member, action_name="Normal Attack")
                    if dmg <= 0:
                        log.info("%s's attack was dodged by %s", member.id, tgt_foe.id)
                    else:
                        log.info("%s hits %s for %s", member.id, tgt_foe.id, dmg)
                        damage_type = getattr(member.damage_type, 'id', 'generic') if hasattr(member, 'damage_type') else 'generic'
                        await BUS.emit_async("hit_landed", member, tgt_foe, dmg, "attack", f"{damage_type}_attack")
                        # Trigger hit_landed passives for the attacker
                        await registry.trigger_hit_landed(member, tgt_foe, dmg, "attack",
                                                        damage_type=damage_type,
                                                        party=combat_party.members,
                                                        foes=foes)
                    tgt_mgr.maybe_inflict_dot(member, dmg)
                    targets_hit = 1
                    if getattr(member.damage_type, "id", "").lower() == "wind":
                        # Compute dynamic scaling based on number of living targets.
                        # Example mapping from N targets -> scale = 1 / (2N):
                        # 4 targets => 1/8, 5 targets => 1/10, etc.
                        try:
                            living_targets = sum(1 for f in foes if getattr(f, "hp", 0) > 0)
                        except Exception:
                            living_targets = len(foes) if isinstance(foes, list) else 1
                        living_targets = max(1, int(living_targets))
                        scale = 1.0 / (2.0 * living_targets)
                        scaled_atk = member.atk * scale
                        for extra_idx, extra_foe in enumerate(foes):
                            if extra_idx == tgt_idx or extra_foe.hp <= 0:
                                await asyncio.sleep(0.001)
                                continue
                            extra_dmg = await extra_foe.apply_damage(
                                scaled_atk, attacker=member, action_name="Wind Spread"
                            )
                            targets_hit += 1
                            if extra_dmg <= 0:
                                log.info(
                                    "%s's attack was dodged by %s",
                                    member.id,
                                    extra_foe.id,
                                )
                            else:
                                log.info(
                                    "%s hits %s for %s",
                                    member.id,
                                    extra_foe.id,
                                    extra_dmg,
                                )
                                await BUS.emit_async("hit_landed", member, extra_foe, extra_dmg, "attack", "wind_multi_attack")
                                # Trigger hit_landed passives for wind multi-attack
                                await registry.trigger_hit_landed(member, extra_foe, extra_dmg, "wind_multi_attack",
                                                                damage_type="wind",
                                                                party=combat_party.members,
                                                                foes=foes)
                            foe_effects[extra_idx].maybe_inflict_dot(member, extra_dmg)
                            await _credit_if_dead(extra_foe)
                            _remove_dead_foes()
                            if not foes:
                                break
                        if not foes:
                            break
                    await BUS.emit_async("action_used", member, tgt_foe, dmg)
                    duration = calc_animation_time(member, targets_hit)
                    if duration > 0:
                        await BUS.emit_async(
                            "animation_start", member, targets_hit, duration
                        )
                        try:
                            await asyncio.sleep(duration)
                        finally:
                            await BUS.emit_async(
                                "animation_end", member, targets_hit, duration
                            )
                    # Trigger action_taken passives for the acting member
                    await registry.trigger("action_taken", member, target=tgt_foe, damage=dmg, party=combat_party.members, foes=foes)
                    # Sync any new summons into party/foes so they can act this round
                    try:
                        # Add party-side summons
                        SummonManager.add_summons_to_party(combat_party)
                        # Add foe-side summons to foes list with effect managers
                        for foe_owner in list(foes):
                            owner_id = getattr(foe_owner, 'id', str(id(foe_owner)))
                            for s in SummonManager.get_summons(owner_id):
                                if s not in foes:
                                    foes.append(s)
                                    mgr = EffectManager(s)
                                    s.effect_manager = mgr
                                    foe_effects.append(mgr)
                                    enrage_mods.append(None)
                    except Exception:
                        pass
                    member.add_ultimate_charge(member.actions_per_turn)
                    for ally in combat_party.members:
                        ally.handle_ally_action(member)
                    if enrage_active:
                        turns_since_enrage = max(enrage_stacks, 0)
                        next_trigger = (enrage_bleed_applies + 1) * 10
                        if turns_since_enrage >= next_trigger:
                            stacks_to_add = 1 + enrage_bleed_applies
                            from autofighter.effects import DamageOverTime
                            for mgr in party_effects:
                                for _ in range(stacks_to_add):
                                    dmg_per_tick = int(max(mgr.stats.max_hp, 1) * 0.10)
                                    mgr.add_dot(
                                        DamageOverTime(
                                            "Enrage Bleed", dmg_per_tick, 10, "enrage_bleed"
                                        )
                                    )
                            for mgr, foe_obj in zip(foe_effects, foes, strict=False):
                                for _ in range(stacks_to_add):
                                    dmg_per_tick = int(max(foe_obj.max_hp, 1) * 0.10)
                                    mgr.add_dot(
                                        DamageOverTime(
                                            "Enrage Bleed", dmg_per_tick, 10, "enrage_bleed"
                                        )
                                    )
                            enrage_bleed_applies += 1
                    await registry.trigger("turn_end", member, party=combat_party.members, foes=foes)
                    await registry.trigger_turn_end(member)
                    member.action_points = max(0, member.action_points - 1)
                    if (
                        _EXTRA_TURNS.get(id(member), 0) > 0
                        and member.hp > 0
                    ):
                        _EXTRA_TURNS[id(member)] -= 1
                        await _pace(action_start)
                        await asyncio.sleep(0.001)
                        continue
                    if progress is not None:
                        await progress(
                            {
                                "result": "battle",
                                "party": [
                                    _serialize(m)
                                    for m in combat_party.members
                                    if not isinstance(m, Summon)
                                ],
                                "foes": [
                                    _serialize(f)
                                    for f in foes
                                    if not isinstance(f, Summon)
                                ],
                                "party_summons": _collect_summons(combat_party.members),
                                "foe_summons": _collect_summons(foes),
                                "enrage": {"active": enrage_active, "stacks": enrage_stacks, "turns": enrage_stacks},
                                "rdr": temp_rdr,
                                "action_queue": _queue_snapshot(),
                                "active_id": member.id,
                            }
                        )
                        _advance_queue(member)
                    await _pace(action_start)
                    if tgt_foe.hp <= 0:
                        await _credit_if_dead(tgt_foe)
                        _remove_dead_foes()
                        await asyncio.sleep(0.001)
                        if not foes:
                            break
                        await asyncio.sleep(0.001)
                        continue
                    await asyncio.sleep(0.001)
                    break
            # End of party member loop
            if not foes:
                break
            # If party wiped during this round, stop taking actions
            if not any(m.hp > 0 for m in combat_party.members):
                break
            # Foes: each living foe takes exactly one action per round
            # Iterate over a snapshot to avoid mutating while iterating
            for foe_idx, acting_foe in enumerate(list(foes)):
                if acting_foe.action_points <= 0:
                    acting_foe.action_points = acting_foe.actions_per_turn
                    for _ in range(max(0, acting_foe.action_points - 1)):
                        try:
                            BUS.emit("extra_turn", acting_foe)
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
                        (idx, m)
                        for idx, m in enumerate(combat_party.members)
                        if m.hp > 0
                    ]
                    if not alive_targets:
                        break
                    weights = [max(m.aggro, 0.0) for _, m in alive_targets]
                    if sum(weights) > 0:
                        pidx, target = random.choices(
                            alive_targets, weights=weights
                        )[0]
                    else:
                        pidx, target = random.choice(alive_targets)
                    target_effect = party_effects[pidx]
                    foe_mgr = foe_effects[foe_idx]
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
                    # Emit BUS event for relics that subscribe to turn_start - async for better performance
                    await BUS.emit_async("turn_start", acting_foe)
                    log.debug("%s turn start targeting %s", acting_foe.id, target.id)
                    await acting_foe.maybe_regain(turn)
                    dt = getattr(acting_foe, "damage_type", None)
                    await foe_mgr.tick(target_effect)
                    # Credit any foes that died from effects applied by foes (e.g., bleed)
                    for f in foes:
                        await _credit_if_dead(f)
                    # Deferring foe removal until after the loop preserves turn order
                    if all(f.hp <= 0 for f in foes):
                        break
                    if acting_foe.hp <= 0:
                        await registry.trigger("turn_end", acting_foe, party=combat_party.members, foes=foes)
                        await asyncio.sleep(0.001)
                        break
                    proceed = await foe_mgr.on_action()
                    if proceed is None:
                        proceed = True
                    if proceed and hasattr(dt, "on_action"):
                        res = await dt.on_action(acting_foe, foes, combat_party.members)
                        proceed = True if res is None else bool(res)
                    if getattr(acting_foe, "ultimate_ready", False) and hasattr(dt, "ultimate"):
                        if hasattr(acting_foe, "use_ultimate") and acting_foe.use_ultimate():
                            try:
                                # Emit ultimate start event for foes
                                await BUS.emit_async("ultimate_used", acting_foe, None, 0, "ultimate", {"ultimate_type": getattr(acting_foe.damage_type, 'id', 'generic'), "caster_type": "foe"})
                                await dt.ultimate(acting_foe, foes, combat_party.members)
                                # Emit ultimate end event for foes
                                await BUS.emit_async("ultimate_completed", acting_foe, None, 0, "ultimate", {"ultimate_type": getattr(acting_foe.damage_type, 'id', 'generic'), "caster_type": "foe"})
                            except Exception as e:
                                # Emit ultimate failed event for foes
                                await BUS.emit_async("ultimate_failed", acting_foe, None, 0, "ultimate", {"ultimate_type": getattr(acting_foe.damage_type, 'id', 'generic'), "caster_type": "foe", "error": str(e)})
                                pass
                    if not proceed:
                        await BUS.emit_async("action_used", acting_foe, acting_foe, 0)
                        acting_foe.add_ultimate_charge(acting_foe.actions_per_turn)
                        await registry.trigger("turn_end", acting_foe, party=combat_party.members, foes=foes)
                        if _EXTRA_TURNS.get(id(acting_foe), 0) > 0 and acting_foe.hp > 0:
                            _EXTRA_TURNS[id(acting_foe)] -= 1
                            await _pace(action_start)
                            continue
                        if progress is not None:
                            await progress(
                                {
                                    "result": "battle",
                                    "party": [
                                        _serialize(m)
                                        for m in combat_party.members
                                        if not isinstance(m, Summon)
                                    ],
                                    "foes": [
                                        _serialize(f)
                                        for f in foes
                                        if not isinstance(f, Summon)
                                    ],
                                    "party_summons": _collect_summons(combat_party.members),
                                    "foe_summons": _collect_summons(foes),
                                    "enrage": {
                                        "active": enrage_active,
                                        "stacks": enrage_stacks,
                                        "turns": enrage_stacks,
                                    },
                                    "rdr": temp_rdr,
                                    "action_queue": _queue_snapshot(),
                                    "active_id": acting_foe.id,
                                }
                            )
                            _advance_queue(acting_foe)
                        await _pace(action_start)
                        await asyncio.sleep(0.001)
                        break
                    dmg = await target.apply_damage(acting_foe.atk, attacker=acting_foe)
                    if dmg <= 0:
                        log.info("%s's attack was dodged by %s", acting_foe.id, target.id)
                    else:
                        log.info("%s hits %s for %s", acting_foe.id, target.id, dmg)
                        damage_type = getattr(acting_foe.damage_type, 'id', 'generic') if hasattr(acting_foe, 'damage_type') else 'generic'
                        await BUS.emit_async("hit_landed", acting_foe, target, dmg, "attack", f"foe_{damage_type}_attack")
                    target_effect.maybe_inflict_dot(acting_foe, dmg)
                    targets_hit = 1
                    await BUS.emit_async("action_used", acting_foe, target, dmg)
                    duration = calc_animation_time(acting_foe, targets_hit)
                    if duration > 0:
                        await BUS.emit_async(
                            "animation_start", acting_foe, targets_hit, duration
                        )
                        try:
                            await asyncio.sleep(duration)
                        finally:
                            await BUS.emit_async(
                                "animation_end", acting_foe, targets_hit, duration
                            )
                    # Trigger action_taken passives for the acting foe
                    await registry.trigger("action_taken", acting_foe)
                    # Sync any new summons created by foes
                    try:
                        SummonManager.add_summons_to_party(combat_party)
                        for foe_owner in list(foes):
                            owner_id = getattr(foe_owner, 'id', str(id(foe_owner)))
                            for s in SummonManager.get_summons(owner_id):
                                if s not in foes:
                                    foes.append(s)
                                    mgr = EffectManager(s)
                                    s.effect_manager = mgr
                                    foe_effects.append(mgr)
                                    enrage_mods.append(None)
                    except Exception:
                        pass
                    acting_foe.add_ultimate_charge(acting_foe.actions_per_turn)
                    # Wind-aligned foes gain charge from ally actions too
                    for ally in foes:
                        ally.handle_ally_action(acting_foe)
                    await registry.trigger("turn_end", acting_foe, party=combat_party.members, foes=foes)
                    await registry.trigger_turn_end(acting_foe)
                    acting_foe.action_points = max(0, acting_foe.action_points - 1)
                    if (
                        _EXTRA_TURNS.get(id(acting_foe), 0) > 0
                        and acting_foe.hp > 0
                    ):
                        _EXTRA_TURNS[id(acting_foe)] -= 1
                        await _pace(action_start)
                        await asyncio.sleep(0.001)
                        continue
                    if progress is not None:
                        await progress(
                            {
                                "result": "battle",
                                "party": [
                                    _serialize(m)
                                    for m in combat_party.members
                                    if not isinstance(m, Summon)
                                ],
                                "foes": [
                                    _serialize(f)
                                    for f in foes
                                    if not isinstance(f, Summon)
                                ],
                                "party_summons": _collect_summons(combat_party.members),
                                "foe_summons": _collect_summons(foes),
                                "enrage": {
                                    "active": enrage_active,
                                    "stacks": enrage_stacks,
                                    "turns": enrage_stacks,
                                },
                                "rdr": temp_rdr,
                                "action_queue": _queue_snapshot(),
                                "active_id": acting_foe.id,
                            }
                        )
                        _advance_queue(acting_foe)
                    await _pace(action_start)
                    await asyncio.sleep(0.001)
                    break
            _remove_dead_foes()
            if not foes:
                break
        # Signal completion as soon as the loop ends to help UIs stop polling
        # immediately, even before rewards are fully computed.
        if progress is not None:
            try:
                await progress(
                    {
                        "result": "battle",
                        "party": [
                            _serialize(m)
                            for m in combat_party.members
                            if not isinstance(m, Summon)
                        ],
                        "foes": [
                            _serialize(f)
                            for f in foes
                            if not isinstance(f, Summon)
                        ],
                        "party_summons": _collect_summons(combat_party.members),
                        "foe_summons": _collect_summons(foes),
                        "enrage": {"active": enrage_active, "stacks": enrage_stacks, "turns": enrage_stacks},
                        "rdr": temp_rdr,
                        "action_queue": _queue_snapshot(),
                        "active_id": None,
                        "ended": True,
                    }
                )
            except Exception:
                pass

        # Emit battle_end for each foe to allow relics/effects to clean up.
        try:
            for foe_obj in foes:
                await BUS.emit_async("battle_end", foe_obj)
        except Exception:
            pass

        # End battle logging
        battle_result = "defeat" if all(m.hp <= 0 for m in combat_party.members) else "victory"
        end_battle_logging(battle_result)

        for mod in enrage_mods:
            if mod is not None:
                mod.remove()
        for member, mgr in zip(combat_party.members, party_effects, strict=False):
            await mgr.cleanup(member)
        for foe_obj, mgr in zip(foes, foe_effects, strict=False):
            await mgr.cleanup(foe_obj)
        # Reset enrage percent after battle ends to avoid leaking to other battles.
        try:
            set_enrage_percent(0.0)
        except Exception:
            pass
        # Mark battle inactive to drop any stray async pings
        try:
            from autofighter.stats import set_battle_active
            set_battle_active(False)
        except Exception:
            pass
        party.members = combat_party.members
        party.gold = combat_party.gold
        party.relics = combat_party.relics
        party.cards = combat_party.cards
        # Award experience to all surviving party members on victory before
        # serializing party state so level/EXP changes are reflected in the
        # response and persisted by save_party.
        if any(m.hp > 0 for m in party.members) and exp_reward > 0:
            for member in party.members:
                try:
                    member.gain_exp(exp_reward)
                except Exception:
                    # Do not let EXP calculation break battle resolution
                    pass
            try:
                level = get_user_level()
                gain_user_exp(int(exp_reward / max(1, level)))
                # Do not reapply global level buffs mid-run; buffs are fixed at run start.
            except Exception:
                pass
        party_data = [_serialize(p) for p in party.members]
        foes_data = [_serialize(f) for f in foes]
        party_summons = _collect_summons(party.members)
        foe_summons = _collect_summons(foes)
        # Ensure summons and related tracking are cleared before exiting the battle
        SummonManager.cleanup()
        if all(m.hp <= 0 for m in combat_party.members):
            loot = {
                "gold": 0,
                "card_choices": [],
                "relic_choices": [],
                "items": [],
            }
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
                "foes": [fd for f, fd in zip(foes, foes_data, strict=False) if not isinstance(f, Summon)],
                "foe_summons": foe_summons,
                "room_number": self.node.index,
                "exp_reward": exp_reward,
                "enrage": {"active": enrage_active, "stacks": enrage_stacks, "turns": enrage_stacks},
                "rdr": temp_rdr,
                "action_queue": _queue_snapshot(),
                "ended": True,
            }
        # Pick cards with per-item star rolls; ensure unique choices not already owned
        selected_cards: list = []
        attempts = 0
        log.info("Starting card selection for run %s, party has %d cards",
                 getattr(combat_party, 'cards', []), len(getattr(combat_party, 'cards', [])))
        while len(selected_cards) < 3 and attempts < 30:
            attempts += 1
            base_stars = _pick_card_stars(self)
            cstars = _apply_rdr_to_stars(base_stars, temp_rdr)
            log.debug("Card selection attempt %d: base_stars=%d, rdr_stars=%d", attempts, base_stars, cstars)
            one = card_choices(combat_party, cstars, count=1)
            log.debug("  card_choices returned %d options", len(one))
            if not one:
                log.debug("  No cards available for star level %d", cstars)
                continue
            c = one[0]
            log.debug("  Candidate card: %s (%s) - %d stars", c.id, c.name, c.stars)
            if any(x.id == c.id for x in selected_cards):
                log.debug("  Card %s already selected, skipping", c.id)
                continue
            selected_cards.append(c)
            log.debug("  Added card: %s", c.id)
        log.info("Card selection complete: %d cards selected after %d attempts", len(selected_cards), attempts)
        if selected_cards:
            log.info("Selected cards: %s", [c.id for c in selected_cards])
        else:
            log.warning("No cards were selected!")
        choice_data = [
            {"id": c.id, "name": c.name, "stars": c.stars, "about": c.about}
            for c in selected_cards
        ]
        relic_opts = []
        if _roll_relic_drop(self, temp_rdr):
            # Offer relics with per-item star rolls; ensure unique choices
            picked: list = []
            tries = 0
            while len(picked) < 3 and tries < 30:
                tries += 1
                rstars = _apply_rdr_to_stars(_pick_relic_stars(self), temp_rdr)
                one = relic_choices(combat_party, rstars, count=1)
                if not one:
                    continue
                r = one[0]
                if any(x.id == r.id for x in picked):
                    continue
                picked.append(r)
            relic_opts = picked

        # Fallback relic system: if no cards are available, provide fallback relic
        if not selected_cards:
            from plugins.relics.fallback_essence import FallbackEssence
            fallback_relic = FallbackEssence()
            if not relic_opts:  # If no regular relic drop, make fallback the only option
                relic_opts = [fallback_relic]
            else:  # If regular relic drop occurred, add fallback as an additional option
                relic_opts.append(fallback_relic)
        relic_choice_data = [
            {
                "id": r.id,
                "name": r.name,
                "stars": r.stars,
                "about": r.describe(party.relics.count(r.id) + 1),
                "stacks": party.relics.count(r.id),
            }
            for r in relic_opts
        ]
        gold_reward = _calc_gold(self, temp_rdr)
        party.gold += gold_reward
        BUS.emit_batched("gold_earned", gold_reward)
        item_base = 1 * temp_rdr
        base_int = int(item_base)
        item_count = max(1, base_int)
        if random.random() < item_base - base_int:
            item_count += 1
        items = [
            {"id": random.choice(ELEMENTS), "stars": _pick_item_stars(self)}
            for _ in range(item_count)
        ]
        ticket_chance = 0.1 * temp_rdr
        if random.random() < ticket_chance:
            items.append({"id": "ticket", "stars": 0})
        loot = {
            "gold": party.gold - start_gold,
            "card_choices": choice_data,
            "relic_choices": relic_choice_data,
            "items": items,
        }
        log.info(
            "Battle rewards: gold=%s cards=%s relics=%s items=%s",
            loot["gold"],
            [c["id"] for c in choice_data],
            [r["id"] for r in relic_choice_data],
            items,
        )
        return {
            "result": "boss" if self.strength > 1.0 else "battle",
            "party": party_data,
            "party_summons": party_summons,
            "gold": party.gold,
            "relics": party.relics,
            "cards": party.cards,
            "card_choices": choice_data,
            "relic_choices": relic_choice_data,
            "loot": loot,
            "foes": [fd for f, fd in zip(foes, foes_data, strict=False) if not isinstance(f, Summon)],
            "foe_summons": foe_summons,
            "room_number": self.node.index,
            "battle_index": getattr(battle_logger, "battle_index", 0),
            "exp_reward": exp_reward,
            "enrage": {"active": enrage_active, "stacks": enrage_stacks, "turns": enrage_stacks},
            "rdr": party.rdr,
            "action_queue": _queue_snapshot(),
            "ended": True,
        }


from .boss import BossRoom  # noqa: E402  # imported for isinstance checks
