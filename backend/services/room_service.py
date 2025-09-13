from __future__ import annotations

import asyncio
import copy
from typing import Any

from battle_logging import get_current_run_logger
from battle_logging import start_run_logging
from game import _run_battle
from game import battle_locks
from game import battle_snapshots
from game import battle_tasks
from game import get_save_manager
from game import load_map
from game import load_party
from game import save_map
from game import save_party

from autofighter.party import Party
from autofighter.rooms import BattleRoom
from autofighter.rooms import BossRoom
from autofighter.rooms import ChatRoom
from autofighter.rooms import RestRoom
from autofighter.rooms import ShopRoom
from autofighter.rooms import _build_foes
from autofighter.rooms import _choose_foe
from autofighter.rooms import _scale_stats
from autofighter.rooms import _serialize
from autofighter.summons.manager import SummonManager
from plugins.damage_types import load_damage_type


def _collect_summons(entities: list) -> dict[str, list[dict[str, Any]]]:
    snapshots: dict[str, list[dict[str, Any]]] = {}
    for ent in entities:
        sid = getattr(ent, "id", str(id(ent)))
        for summon in SummonManager.get_summons(sid):
            snap = _serialize(summon)
            snap["owner_id"] = sid
            snapshots.setdefault(sid, []).append(snap)
    return snapshots


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
                    foes = _build_foes(node, party)
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
        foes = _build_foes(node, party)
        for f in foes:
            _scale_stats(f, node, room.strength)
        combat_party = Party(
            members=[copy.deepcopy(m) for m in party.members],
            gold=party.gold,
            relics=party.relics,
            cards=party.cards,
            rdr=party.rdr,
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
    room = ShopRoom(node)
    party = await asyncio.to_thread(load_party, run_id)
    result = await room.resolve(party, data)
    stock_state[str(node.room_id)] = getattr(node, "stock", [])
    state["shop_stock"] = stock_state
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


async def rest_room(run_id: str, data: dict[str, Any]) -> dict[str, Any]:
    state, rooms = await asyncio.to_thread(load_map, run_id)
    if not rooms or not (0 <= int(state.get("current", 0)) < len(rooms)):
        raise LookupError("run ended or room out of range")
    node = rooms[state["current"]]
    if node.room_type != "rest":
        raise ValueError("invalid room")
    room = RestRoom(node)
    party = await asyncio.to_thread(load_party, run_id)
    result = await room.resolve(party, data)
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
        foe = _choose_foe(party)
        _scale_stats(foe, node, room.strength)
        foes = [foe]
        combat_party = Party(
            members=[copy.deepcopy(m) for m in party.members],
            gold=party.gold,
            relics=party.relics,
            cards=party.cards,
            rdr=party.rdr,
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
    if room_type == "rest":
        return await rest_room(run_id, request_data)
    if room_type == "chat":
        return await chat_room(run_id, request_data)
    raise ValueError(f"Unsupported room type: {room_type}")
