from __future__ import annotations

import asyncio
import copy
import random
from typing import Any

from battle_logging.writers import get_current_run_logger
from battle_logging.writers import start_run_logging
from runs.encryption import get_save_manager
from runs.lifecycle import _run_battle
from runs.lifecycle import battle_locks
from runs.lifecycle import battle_snapshots
from runs.lifecycle import battle_tasks
from runs.lifecycle import load_map
from runs.lifecycle import save_map
from runs.party_manager import load_party
from runs.party_manager import save_party

from autofighter.party import Party
from autofighter.rooms import BattleRoom
from autofighter.rooms import BossRoom
from autofighter.rooms import ChatRoom
from autofighter.rooms import ShopRoom
from autofighter.rooms import _build_foes
from autofighter.rooms import _choose_foe
from autofighter.rooms import _scale_stats
from autofighter.rooms import _serialize
from autofighter.rooms import calculate_rank_probabilities
from autofighter.summons.manager import SummonManager
from plugins import foes as foe_plugins
from plugins.damage_types import load_damage_type


def _boss_matches_node(info: Any, node: Any) -> bool:
    try:
        return (
            isinstance(info, dict)
            and info.get("id")
            and int(info.get("floor", -1)) == int(getattr(node, "floor", -1))
            and int(info.get("loop", -1)) == int(getattr(node, "loop", -1))
        )
    except Exception:
        return False


def _instantiate_boss(foe_id: str | None):
    if not foe_id:
        return None
    try:
        for name in getattr(foe_plugins, "__all__", []):
            cls = getattr(foe_plugins, name, None)
            if cls is not None and getattr(cls, "id", None) == foe_id:
                return cls()
    except Exception:
        pass
    try:
        foe_cls = foe_plugins.PLAYER_FOES.get(foe_id)
        if foe_cls is not None:
            return foe_cls()
    except Exception:
        pass
    return None


def _collect_summons(entities: list) -> dict[str, list[dict[str, Any]]]:
    snapshots: dict[str, list[dict[str, Any]]] = {}
    for ent in entities:
        sid = getattr(ent, "id", str(id(ent)))
        for summon in SummonManager.get_summons(sid):
            snap = _serialize(summon)
            snap["owner_id"] = sid
            snapshots.setdefault(sid, []).append(snap)
    return snapshots


def _normalize_recent_foes(
    state: dict[str, Any],
) -> tuple[list[dict[str, int]], set[str], bool]:
    entries = state.get("recent_foes", [])
    changed = False
    if not isinstance(entries, list):
        if entries:
            changed = True
        return [], set(), changed

    ordered_ids: list[str] = []
    aggregated: dict[str, int] = {}

    for entry in entries:
        if not isinstance(entry, dict):
            changed = True
            continue
        foe_id = entry.get("id")
        if not foe_id:
            changed = True
            continue
        try:
            cooldown = int(entry.get("cooldown", 0))
        except Exception:
            changed = True
            continue
        if cooldown <= 0:
            changed = True
            continue
        foe_key = str(foe_id)
        if foe_key not in aggregated:
            ordered_ids.append(foe_key)
            aggregated[foe_key] = cooldown
        else:
            prev = aggregated[foe_key]
            if cooldown > prev:
                aggregated[foe_key] = cooldown
                changed = True
            elif cooldown != prev:
                changed = True

    normalized = [{"id": foe_id, "cooldown": aggregated[foe_id]} for foe_id in ordered_ids]
    if len(normalized) != len(entries):
        changed = True
    return normalized, set(ordered_ids), changed


async def battle_room(run_id: str, data: dict[str, Any]) -> dict[str, Any]:
    action = data.get("action", "")

    if action == "snapshot":
        snap = battle_snapshots.get(run_id)
        if snap is not None:
            return snap
        action = ""
        data = {k: v for k, v in data.items() if k != "action"}

    if action == "pause":
        if run_id in battle_tasks:
            task = battle_tasks[run_id]
            if not task.done():
                task.cancel()
            snap = battle_snapshots.get(run_id, {})
            snap["paused"] = True
            battle_snapshots[run_id] = snap
        return {"result": "paused"}

    if action == "resume":
        snap = battle_snapshots.get(run_id)
        if snap and snap.get("paused"):
            snap["paused"] = False
            battle_snapshots[run_id] = snap
            if run_id not in battle_tasks or battle_tasks[run_id].done():
                party = await asyncio.to_thread(load_party, run_id)
                state, rooms = await asyncio.to_thread(load_map, run_id)
                if rooms and 0 <= int(state.get("current", 0)) < len(rooms):
                    node = rooms[state["current"]]
                    room = BattleRoom(node)
                    normalized, recent_ids, changed = _normalize_recent_foes(state)
                    if changed:
                        state["recent_foes"] = normalized
                        await asyncio.to_thread(save_map, run_id, state)
                    progression = {
                        "total_rooms_cleared": state.get("total_rooms_cleared", 0),
                        "floors_cleared": state.get("floors_cleared", 0),
                        "current_pressure": state.get(
                            "current_pressure",
                            getattr(node, "pressure", 0),
                        ),
                    }
                    foes = _build_foes(
                        node,
                        party,
                        recent_ids=recent_ids,
                        progression=progression,
                    )
                    for f in foes:
                        _scale_stats(f, node, room.strength)
                    combat_party = Party(
                        members=[copy.deepcopy(m) for m in party.members],
                        gold=party.gold,
                        relics=party.relics,
                        cards=party.cards,
                        rdr=party.rdr,
                    )

                    async def progress(snapshot: dict[str, Any]) -> None:
                        battle_snapshots[run_id] = snapshot

                    task = asyncio.create_task(
                        _run_battle(run_id, room, foes, combat_party, {}, state, rooms, progress)
                    )
                    battle_tasks[run_id] = task
        return {"result": "resumed"}

    party = await asyncio.to_thread(load_party, run_id)
    try:
        with get_save_manager().connection() as conn:
            row = conn.execute(
                "SELECT type FROM damage_types WHERE id = ?", ("player",)
            ).fetchone()
        if row and row[0]:
            for m in party.members:
                if m.id == "player":
                    m.damage_type = load_damage_type(row[0])
                    break
    except Exception:
        pass
    state, rooms = await asyncio.to_thread(load_map, run_id)
    try:
        logger = get_current_run_logger()
        if logger is None or getattr(logger, "run_id", None) != run_id:
            start_run_logging(run_id)
    except Exception:
        pass
    if not rooms or not (0 <= int(state.get("current", 0)) < len(rooms)):
        snap = battle_snapshots.get(run_id)
        if snap is not None:
            return snap
        # If no rooms and no snapshot, the run likely ended or was deleted
        # Return an error instead of creating a phantom battle
        raise LookupError("run ended or room out of range")
    node = rooms[state["current"]]
    if node.room_type not in {"battle-weak", "battle-normal"}:
        raise ValueError("invalid room")
    normalized_recent, recent_ids, recent_changed = _normalize_recent_foes(state)
    if recent_changed:
        state["recent_foes"] = normalized_recent
        await asyncio.to_thread(save_map, run_id, state)
    # Check awaiting flags before attempting to launch a new battle
    awaiting_card = state.get("awaiting_card")
    awaiting_relic = state.get("awaiting_relic")
    awaiting_loot = state.get("awaiting_loot")
    awaiting_next = state.get("awaiting_next")

    if awaiting_next:
        snap = battle_snapshots.get(run_id)
        if snap is not None:
            return snap
        party_data = [_serialize(m) for m in party.members]
        payload: dict[str, Any] = {
            "result": "battle",
            "party": party_data,
            "foes": [],
            "gold": party.gold,
            "relics": party.relics,
            "cards": party.cards,
            "card_choices": [],
            "relic_choices": [],
            "enrage": {"active": False, "stacks": 0},
            "rdr": party.rdr,
        }
        next_type = (
            rooms[state["current"] + 1].room_type
            if state["current"] + 1 < len(rooms)
            else None
        )
        payload.update(
            {
                "awaiting_next": True,
                "current_index": state.get("current", 0),
                "current_room": node.room_type,
            }
        )
        if next_type is not None:
            payload["next_room"] = next_type
        return payload

    if awaiting_card or awaiting_relic or awaiting_loot:
        snap = battle_snapshots.get(run_id)
        if snap is not None:
            return snap
    if run_id in battle_tasks and not battle_tasks[run_id].done():
        snap = battle_snapshots.get(run_id, {"result": "battle"})
        return snap
    lock = battle_locks.setdefault(run_id, asyncio.Lock())
    async with lock:
        if run_id in battle_tasks and not battle_tasks[run_id].done():
            return battle_snapshots.get(run_id, {"result": "battle"})
        state["battle"] = True
        await asyncio.to_thread(save_map, run_id, state)
        room = BattleRoom(node)
        boss_info = state.get("floor_boss")
        exclude_ids = None
        if _boss_matches_node(boss_info, node):
            boss_id = boss_info.get("id") if isinstance(boss_info, dict) else None
            if boss_id:
                exclude_ids = {boss_id}
        progression = {
            "total_rooms_cleared": state.get("total_rooms_cleared", 0),
            "floors_cleared": state.get("floors_cleared", 0),
            "current_pressure": state.get(
                "current_pressure",
                getattr(node, "pressure", 0),
            ),
        }
        foes = _build_foes(
            node,
            party,
            exclude_ids=exclude_ids,
            recent_ids=recent_ids,
            progression=progression,
        )
        for f in foes:
            _scale_stats(f, node, room.strength)
        combat_party = Party(
            members=[copy.deepcopy(m) for m in party.members],
            gold=party.gold,
            relics=party.relics,
            cards=party.cards,
            rdr=party.rdr,
            no_shops=getattr(party, "no_shops", False),
            no_rests=getattr(party, "no_rests", False),
        )
        if hasattr(party, "pull_tokens"):
            combat_party.pull_tokens = getattr(party, "pull_tokens", 0)
        if hasattr(party, "_null_lantern_cleared"):
            setattr(
                combat_party,
                "_null_lantern_cleared",
                getattr(party, "_null_lantern_cleared", 0),
            )
        battle_snapshots[run_id] = {
            "result": "battle",
            "party": [_serialize(m) for m in combat_party.members],
            "foes": [_serialize(f) for f in foes],
            "party_summons": _collect_summons(combat_party.members),
            "foe_summons": _collect_summons(foes),
            "gold": party.gold,
            "relics": party.relics,
            "cards": party.cards,
            "card_choices": [],
            "relic_choices": [],
            "enrage": {"active": False, "stacks": 0},
            "rdr": party.rdr,
        }
        state["battle"] = False
        await asyncio.to_thread(save_map, run_id, state)

        async def progress(snapshot: dict[str, Any]) -> None:
            battle_snapshots[run_id] = snapshot

        task = asyncio.create_task(
            _run_battle(run_id, room, foes, party, data, state, rooms, progress)
        )
        battle_tasks[run_id] = task
        result = battle_snapshots[run_id]
    return result


async def shop_room(run_id: str, data: dict[str, Any]) -> dict[str, Any]:
    state, rooms = await asyncio.to_thread(load_map, run_id)
    if not rooms or not (0 <= int(state.get("current", 0)) < len(rooms)):
        snap = battle_snapshots.get(run_id)
        if snap is not None:
            return snap
        raise LookupError("run ended or room out of range")
    node = rooms[state["current"]]
    if node.room_type != "shop":
        raise ValueError("invalid room")
    stock_state = state.setdefault("shop_stock", {})
    node_stock = stock_state.get(str(node.room_id))
    if node_stock is not None:
        setattr(node, "stock", node_stock)
    items_bought = int(state.get("shop_items_bought", 0))
    setattr(node, "items_bought", items_bought)
    room = ShopRoom(node)
    party = await asyncio.to_thread(load_party, run_id)
    result = await room.resolve(party, data)
    stock_state[str(node.room_id)] = getattr(node, "stock", [])
    state["shop_stock"] = stock_state
    state["shop_items_bought"] = int(getattr(node, "items_bought", items_bought))
    action = data.get("action", "")
    next_type = None
    if action == "leave":
        state["awaiting_next"] = True
        next_type = (
            rooms[state["current"] + 1].room_type
            if state["current"] + 1 < len(rooms)
            else None
        )
    else:
        state["awaiting_next"] = False
    await asyncio.to_thread(save_map, run_id, state)
    await asyncio.to_thread(save_party, run_id, party)
    payload = {**result}
    if next_type is not None:
        payload["next_room"] = next_type
    return payload


async def chat_room(run_id: str, data: dict[str, Any]) -> dict[str, Any]:
    state, rooms = await asyncio.to_thread(load_map, run_id)
    if not rooms or not (0 <= int(state.get("current", 0)) < len(rooms)):
        raise LookupError("run ended or room out of range")
    node = rooms[state["current"]]
    if node.room_type != "chat":
        raise ValueError("invalid room")
    room = ChatRoom(node)
    party = await asyncio.to_thread(load_party, run_id)
    result = await room.resolve(party, data)
    state["awaiting_next"] = True
    next_type = (
        rooms[state["current"] + 1].room_type
        if state["current"] + 1 < len(rooms)
        else None
    )
    await asyncio.to_thread(save_map, run_id, state)
    await asyncio.to_thread(save_party, run_id, party)
    return {**result, "next_room": next_type}


async def boss_room(run_id: str, data: dict[str, Any]) -> dict[str, Any]:
    action = data.get("action", "")

    # Flag to track if this is a restart scenario (snapshot requested but none exists)
    is_restart_scenario = False

    if action == "snapshot":
        snap = battle_snapshots.get(run_id)
        if snap is not None:
            return snap
        is_restart_scenario = True
        action = ""
        data = {k: v for k, v in data.items() if k != "action"}

    state, rooms = await asyncio.to_thread(load_map, run_id)
    try:
        logger = get_current_run_logger()
        if logger is None or getattr(logger, "run_id", None) != run_id:
            start_run_logging(run_id)
    except Exception:
        pass
    if not rooms or not (0 <= int(state.get("current", 0)) < len(rooms)):
        snap = battle_snapshots.get(run_id)
        if snap is not None:
            return snap
        raise LookupError("run ended or room out of range")
    node = rooms[state["current"]]
    if node.room_type != "battle-boss-floor":
        raise ValueError("invalid room")
    if state.get("awaiting_next"):
        next_type = (
            rooms[state["current"] + 1].room_type
            if state["current"] + 1 < len(rooms)
            else None
        )
        payload: dict[str, Any] = {
            "result": "boss",
            "awaiting_next": True,
            "current_index": state.get("current", 0),
            "current_room": node.room_type,
        }
        if next_type is not None:
            payload["next_room"] = next_type
        return payload

    # Only check awaiting flags if this is NOT a restart scenario
    if not is_restart_scenario and (state.get("awaiting_card") or state.get("awaiting_relic") or state.get("awaiting_loot")):
        snap = battle_snapshots.get(run_id)
        if snap is not None:
            return snap
        party = await asyncio.to_thread(load_party, run_id)
        party_data = [_serialize(m) for m in party.members]
        return {
            "result": "boss",
            "party": party_data,
            "foes": [],
            "gold": party.gold,
            "relics": party.relics,
            "cards": party.cards,
            "card_choices": [],
            "relic_choices": [],
            "enrage": {"active": False, "stacks": 0},
        }
    if run_id in battle_tasks and not battle_tasks[run_id].done():
        return battle_snapshots.get(run_id, {"result": "boss"})
    lock = battle_locks.setdefault(run_id, asyncio.Lock())
    async with lock:
        if run_id in battle_tasks and not battle_tasks[run_id].done():
            return battle_snapshots.get(run_id, {"result": "boss"})
        state["battle"] = True
        await asyncio.to_thread(save_map, run_id, state)
        room = BossRoom(node)
        party = await asyncio.to_thread(load_party, run_id)
        boss_info = state.get("floor_boss")
        foe = None
        if _boss_matches_node(boss_info, node):
            boss_id = boss_info.get("id") if isinstance(boss_info, dict) else None
            foe = _instantiate_boss(boss_id)
        if foe is None:
            foe = _choose_foe(node, party)
            state["floor_boss"] = {
                "id": getattr(foe, "id", type(foe).__name__),
                "floor": getattr(node, "floor", 1),
                "loop": getattr(node, "loop", 1),
            }
        progression = {
            "total_rooms_cleared": state.get("total_rooms_cleared", 0),
            "floors_cleared": state.get("floors_cleared", 0),
            "current_pressure": state.get(
                "current_pressure",
                getattr(node, "pressure", 0),
            ),
        }
        prime_chance, glitched_chance = calculate_rank_probabilities(
            progression["total_rooms_cleared"],
            progression["floors_cleared"],
            progression["current_pressure"],
        )
        forced_prime = "prime" in node.room_type
        forced_glitched = "glitched" in node.room_type
        is_prime = forced_prime
        is_glitched = forced_glitched
        if not is_prime and prime_chance > 0.0:
            is_prime = random.random() < prime_chance
        if not is_glitched and glitched_chance > 0.0:
            is_glitched = random.random() < glitched_chance
        if is_prime and is_glitched:
            foe.rank = "glitched prime boss"
        elif is_prime:
            foe.rank = "prime boss"
        elif is_glitched:
            foe.rank = "glitched boss"
        else:
            foe.rank = "boss"
        _scale_stats(foe, node, room.strength)
        foes = [foe]
        combat_party = Party(
            members=[copy.deepcopy(m) for m in party.members],
            gold=party.gold,
            relics=party.relics,
            cards=party.cards,
            rdr=party.rdr,
            no_shops=getattr(party, "no_shops", False),
            no_rests=getattr(party, "no_rests", False),
        )
        if hasattr(party, "pull_tokens"):
            combat_party.pull_tokens = getattr(party, "pull_tokens", 0)
        if hasattr(party, "_null_lantern_cleared"):
            setattr(
                combat_party,
                "_null_lantern_cleared",
                getattr(party, "_null_lantern_cleared", 0),
            )
        battle_snapshots[run_id] = {
            "result": "boss",
            "party": [_serialize(m) for m in combat_party.members],
            "foes": [_serialize(f) for f in foes],
            "party_summons": _collect_summons(combat_party.members),
            "foe_summons": _collect_summons(foes),
            "gold": party.gold,
            "relics": party.relics,
            "cards": party.cards,
            "card_choices": [],
            "relic_choices": [],
            "enrage": {"active": False, "stacks": 0},
            "rdr": party.rdr,
        }
        state["battle"] = False
        await asyncio.to_thread(save_map, run_id, state)

        async def progress(snapshot: dict[str, Any]) -> None:
            battle_snapshots[run_id] = snapshot

        task = asyncio.create_task(
            _run_battle(run_id, room, foes, party, data, state, rooms, progress)
        )
        battle_tasks[run_id] = task
        result = battle_snapshots[run_id]
    return result


async def room_action(run_id: str, room_id: str, action_data: dict[str, Any] | None = None) -> dict[str, Any]:
    if action_data is None:
        action_data = {}
    state, rooms = await asyncio.to_thread(load_map, run_id)
    if not rooms or not (0 <= int(state.get("current", 0)) < len(rooms)):
        raise ValueError("No current room or run ended")
    current_node = rooms[int(state.get("current", 0))]
    room_type = current_node.room_type
    if action_data.get("type") == "battle" and action_data.get("action_type") == "start":
        request_data = {"action": ""}
    else:
        request_data = action_data
    if room_type in {"battle-weak", "battle-normal"}:
        return await battle_room(run_id, request_data)
    if room_type == "battle-boss-floor":
        return await boss_room(run_id, request_data)
    if room_type == "shop":
        return await shop_room(run_id, request_data)
    if room_type == "chat":
        return await chat_room(run_id, request_data)
    if room_type == "rest":
        raise LookupError("run ended or room out of range")
    raise ValueError(f"Unsupported room type: {room_type}")
