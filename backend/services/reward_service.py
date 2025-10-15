from __future__ import annotations

import asyncio
from typing import Any

from runs.lifecycle import battle_snapshots
from runs.lifecycle import ensure_reward_staging
from runs.lifecycle import load_map
from runs.lifecycle import save_map
from runs.party_manager import load_party
from runs.party_manager import save_party

from autofighter.cards import award_card
from autofighter.cards import instantiate_card
from autofighter.relics import award_relic
from autofighter.relics import instantiate_relic
from tracking import log_game_action


def _serialise_staging(staging: dict[str, Any]) -> dict[str, list[object]]:
    """Return a copy of the staging payload with detached lists."""

    buckets = ("cards", "relics", "items")
    payload: dict[str, list[object]] = {}
    for bucket in buckets:
        values = staging.get(bucket, []) if isinstance(staging, dict) else []
        if isinstance(values, list):
            copied: list[object] = []
            for value in values:
                if isinstance(value, dict):
                    copied.append(dict(value))
                else:
                    copied.append(value)
            payload[bucket] = copied
        else:
            payload[bucket] = []
    return payload


async def select_card(run_id: str, card_id: str) -> dict[str, Any]:
    if not card_id:
        raise ValueError("invalid card")
    party = await asyncio.to_thread(load_party, run_id)
    if card_id in getattr(party, "cards", []):
        raise ValueError("invalid card")

    card = instantiate_card(card_id)
    if card is None:
        raise ValueError("invalid card")

    state, rooms = await asyncio.to_thread(load_map, run_id)
    staging, _ = ensure_reward_staging(state)

    current_index = int(state.get("current", 0))
    room = rooms[current_index] if 0 <= current_index < len(rooms) else None
    room_identifier = str(getattr(room, "room_id", getattr(room, "index", current_index)))

    staged_card: dict[str, Any] = {
        "id": card.id,
        "name": card.name,
        "stars": card.stars,
    }
    about = getattr(card, "about", None)
    if about:
        staged_card["about"] = about

    staging["cards"] = [staged_card]

    awarded_card = award_card(party, card_id)
    if awarded_card is None:
        raise ValueError("invalid card")

    progression = state.get("reward_progression")
    if progression and progression.get("current_step") == "card":
        completed = progression.setdefault("completed", [])
        if "card" not in completed:
            completed.append("card")
        available = progression.get("available", [])
        next_steps = [step for step in available if step not in completed]
        if next_steps:
            progression["current_step"] = next_steps[0]
            state["awaiting_card"] = False
            state["awaiting_next"] = False
        else:
            progression["current_step"] = None
            state["awaiting_card"] = False
            state["awaiting_next"] = True
            state.pop("reward_progression", None)
    else:
        state["awaiting_card"] = False
        if not state.get("awaiting_relic") and not state.get("awaiting_loot"):
            state["awaiting_next"] = True

    await asyncio.to_thread(save_map, run_id, state)
    await asyncio.to_thread(save_party, run_id, party)

    snap = battle_snapshots.get(run_id)
    if isinstance(snap, dict):
        snapshot = dict(snap)
        ensure_reward_staging(snapshot)
        snapshot["card_choices"] = []
        snapshot["awaiting_card"] = state.get("awaiting_card", False)
        snapshot["awaiting_relic"] = state.get("awaiting_relic", False)
        snapshot["awaiting_loot"] = state.get("awaiting_loot", False)
        snapshot["awaiting_next"] = state.get("awaiting_next", False)
        progression_snapshot = state.get("reward_progression")
        if isinstance(progression_snapshot, dict):
            snapshot["reward_progression"] = dict(progression_snapshot)
        else:
            snapshot["reward_progression"] = progression_snapshot
        snapshot_staging = snapshot.get("reward_staging")
        if isinstance(snapshot_staging, dict):
            snapshot_staging.update(_serialise_staging(staging))
        else:
            snapshot["reward_staging"] = _serialise_staging(staging)
        battle_snapshots[run_id] = snapshot

    try:
        await log_game_action(
            "select_card",
            run_id=run_id,
            room_id=room_identifier,
            details={"card": staged_card, "staged": True},
        )
    except Exception:
        pass

    payload = {
        "card": staged_card,
        "cards": list(party.cards),
        "reward_staging": _serialise_staging(staging),
        "awaiting_card": state.get("awaiting_card", False),
        "awaiting_relic": state.get("awaiting_relic", False),
        "awaiting_loot": state.get("awaiting_loot", False),
        "awaiting_next": state.get("awaiting_next", False),
        "reward_progression": state.get("reward_progression"),
    }

    next_index = current_index + 1
    if isinstance(rooms, list) and 0 <= next_index < len(rooms):
        payload["next_room"] = rooms[next_index].room_type

    return payload


async def select_relic(run_id: str, relic_id: str) -> dict[str, Any]:
    if not relic_id:
        raise ValueError("invalid relic")
    party = await asyncio.to_thread(load_party, run_id)

    relic = instantiate_relic(relic_id)
    if relic is None:
        raise ValueError("invalid relic")

    state, rooms = await asyncio.to_thread(load_map, run_id)
    staging, _ = ensure_reward_staging(state)

    current_index = int(state.get("current", 0))
    room = rooms[current_index] if 0 <= current_index < len(rooms) else None
    room_identifier = str(getattr(room, "room_id", getattr(room, "index", current_index)))

    existing_stacks = party.relics.count(relic.id)
    staged_relic: dict[str, Any] = {
        "id": relic.id,
        "name": relic.name,
        "stars": relic.stars,
        "stacks": existing_stacks,
    }
    about = relic.describe(existing_stacks + 1)
    if about:
        staged_relic["about"] = about

    staging["relics"] = [staged_relic]

    awarded_relic = award_relic(party, relic_id)
    if awarded_relic is None:
        raise ValueError("invalid relic")

    staged_relic["stacks"] = party.relics.count(relic.id)

    progression = state.get("reward_progression")
    if progression and progression.get("current_step") == "relic":
        completed = progression.setdefault("completed", [])
        if "relic" not in completed:
            completed.append("relic")
        available = progression.get("available", [])
        next_steps = [step for step in available if step not in completed]
        if next_steps:
            progression["current_step"] = next_steps[0]
            state["awaiting_relic"] = False
            state["awaiting_next"] = False
        else:
            progression["current_step"] = None
            state["awaiting_relic"] = False
            state["awaiting_next"] = True
            state.pop("reward_progression", None)
    else:
        state["awaiting_relic"] = False
        if not state.get("awaiting_card") and not state.get("awaiting_loot"):
            state["awaiting_next"] = True

    await asyncio.to_thread(save_map, run_id, state)
    await asyncio.to_thread(save_party, run_id, party)

    snap = battle_snapshots.get(run_id)
    if isinstance(snap, dict):
        snapshot = dict(snap)
        ensure_reward_staging(snapshot)
        snapshot["relic_choices"] = []
        snapshot["awaiting_card"] = state.get("awaiting_card", False)
        snapshot["awaiting_relic"] = state.get("awaiting_relic", False)
        snapshot["awaiting_loot"] = state.get("awaiting_loot", False)
        snapshot["awaiting_next"] = state.get("awaiting_next", False)
        progression_snapshot = state.get("reward_progression")
        if isinstance(progression_snapshot, dict):
            snapshot["reward_progression"] = dict(progression_snapshot)
        else:
            snapshot["reward_progression"] = progression_snapshot
        snapshot_staging = snapshot.get("reward_staging")
        if isinstance(snapshot_staging, dict):
            snapshot_staging.update(_serialise_staging(staging))
        else:
            snapshot["reward_staging"] = _serialise_staging(staging)
        battle_snapshots[run_id] = snapshot

    try:
        await log_game_action(
            "select_relic",
            run_id=run_id,
            room_id=room_identifier,
            details={"relic": staged_relic, "staged": True},
        )
    except Exception:
        pass

    payload = {
        "relic": staged_relic,
        "relics": list(party.relics),
        "reward_staging": _serialise_staging(staging),
        "awaiting_card": state.get("awaiting_card", False),
        "awaiting_relic": state.get("awaiting_relic", False),
        "awaiting_loot": state.get("awaiting_loot", False),
        "awaiting_next": state.get("awaiting_next", False),
        "reward_progression": state.get("reward_progression"),
    }

    next_index = current_index + 1
    if isinstance(rooms, list) and 0 <= next_index < len(rooms):
        payload["next_room"] = rooms[next_index].room_type

    return payload


async def acknowledge_loot(run_id: str) -> dict[str, Any]:
    state, rooms = await asyncio.to_thread(load_map, run_id)
    if not state.get("awaiting_loot"):
        raise ValueError("not awaiting loot")
    current_index = int(state.get("current", 0))
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
    try:
        await log_game_action(
            "acknowledge_loot",
            run_id=run_id,
            room_id=str(getattr(rooms[current_index], "room_id", current_index)) if rooms else str(current_index),
            details={"next_room": next_type},
        )
    except Exception:
        pass
    return {"next_room": next_type} if next_type is not None else {"next_room": None}
