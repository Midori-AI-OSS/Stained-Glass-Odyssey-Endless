from __future__ import annotations

import asyncio
from typing import Any

from runs.lifecycle import battle_snapshots
from runs.lifecycle import load_map
from runs.lifecycle import save_map
from runs.party_manager import load_party
from runs.party_manager import save_party

from autofighter.cards import award_card
from autofighter.relics import award_relic


async def select_card(run_id: str, card_id: str) -> dict[str, Any]:
    if not card_id:
        raise ValueError("invalid card")
    party = await asyncio.to_thread(load_party, run_id)
    card = award_card(party, card_id)
    if card is None:
        raise ValueError("invalid card")
    state, rooms = await asyncio.to_thread(load_map, run_id)
    progression = state.get("reward_progression")
    if progression and progression.get("current_step") == "card":
        progression["completed"].append("card")
        available = progression.get("available", [])
        completed = progression.get("completed", [])
        next_steps = [step for step in available if step not in completed]
        if next_steps:
            progression["current_step"] = next_steps[0]
            state["awaiting_card"] = False
            state["awaiting_next"] = False
        else:
            progression["current_step"] = None
            state["awaiting_card"] = False
            state["awaiting_next"] = True
            del state["reward_progression"]
    else:
        state["awaiting_card"] = False
        if not state.get("awaiting_relic") and not state.get("awaiting_loot"):
            state["awaiting_next"] = True
    next_type = (
        rooms[state["current"] + 1].room_type
        if state["current"] + 1 < len(rooms) and state.get("awaiting_next")
        else None
    )
    await asyncio.to_thread(save_map, run_id, state)
    await asyncio.to_thread(save_party, run_id, party)
    try:
        snap = battle_snapshots.get(run_id)
        if isinstance(snap, dict):
            snap = dict(snap)
            snap["card_choices"] = []
            battle_snapshots[run_id] = snap
    except Exception:
        pass
    card_data = {"id": card.id, "name": card.name, "stars": card.stars}
    payload = {"card": card_data, "cards": party.cards}
    if next_type is not None:
        payload["next_room"] = next_type
    return payload


async def select_relic(run_id: str, relic_id: str) -> dict[str, Any]:
    if not relic_id:
        raise ValueError("invalid relic")
    party = await asyncio.to_thread(load_party, run_id)
    relic = award_relic(party, relic_id)
    if relic is None:
        raise ValueError("invalid relic")
    state, rooms = await asyncio.to_thread(load_map, run_id)
    progression = state.get("reward_progression")
    if progression and progression.get("current_step") == "relic":
        progression["completed"].append("relic")
        available = progression.get("available", [])
        completed = progression.get("completed", [])
        next_steps = [step for step in available if step not in completed]
        if next_steps:
            progression["current_step"] = next_steps[0]
            state["awaiting_relic"] = False
            state["awaiting_next"] = False
        else:
            progression["current_step"] = None
            state["awaiting_relic"] = False
            state["awaiting_next"] = True
            del state["reward_progression"]
    else:
        state["awaiting_relic"] = False
        if not state.get("awaiting_card") and not state.get("awaiting_loot"):
            state["awaiting_next"] = True
    next_type = (
        rooms[state["current"] + 1].room_type
        if state["current"] + 1 < len(rooms) and state.get("awaiting_next")
        else None
    )
    await asyncio.to_thread(save_map, run_id, state)
    await asyncio.to_thread(save_party, run_id, party)
    try:
        snap = battle_snapshots.get(run_id)
        if isinstance(snap, dict):
            snap = dict(snap)
            snap["relic_choices"] = []
            battle_snapshots[run_id] = snap
    except Exception:
        pass
    relic_data = {"id": relic.id, "name": relic.name, "stars": relic.stars}
    payload = {"relic": relic_data, "relics": party.relics}
    if next_type is not None:
        payload["next_room"] = next_type
    return payload


async def acknowledge_loot(run_id: str) -> dict[str, Any]:
    state, rooms = await asyncio.to_thread(load_map, run_id)
    if not state.get("awaiting_loot"):
        raise ValueError("not awaiting loot")
    progression = state.get("reward_progression")
    if progression and progression.get("current_step") == "loot":
        progression["completed"].append("loot")
        available = progression.get("available", [])
        completed = progression.get("completed", [])
        next_steps = [step for step in available if step not in completed]
        if next_steps:
            progression["current_step"] = next_steps[0]
            state["awaiting_loot"] = False
            state["awaiting_next"] = False
        else:
            progression["current_step"] = None
            state["awaiting_loot"] = False
            state["awaiting_next"] = True
            del state["reward_progression"]
    else:
        state["awaiting_loot"] = False
        if not state.get("awaiting_card") and not state.get("awaiting_relic"):
            state["awaiting_next"] = True
    next_type = (
        rooms[state["current"] + 1].room_type
        if state["current"] + 1 < len(rooms) and state.get("awaiting_next")
        else None
    )
    await asyncio.to_thread(save_map, run_id, state)
    await asyncio.to_thread(save_party, run_id, await asyncio.to_thread(load_party, run_id))
    return {"next_room": next_type} if next_type is not None else {"next_room": None}
