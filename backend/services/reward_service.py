from __future__ import annotations

import asyncio
from datetime import datetime
from datetime import timezone
from typing import Any
from uuid import uuid4

from runs.lifecycle import battle_snapshots
from runs.lifecycle import ensure_reward_progression
from runs.lifecycle import ensure_reward_staging
from runs.lifecycle import load_map
from runs.lifecycle import normalise_reward_step
from runs.lifecycle import reward_locks
from runs.lifecycle import save_map
from runs.lifecycle import REWARD_STEP_CARDS
from runs.lifecycle import REWARD_STEP_DROPS
from runs.lifecycle import REWARD_STEP_RELICS
from runs.party_manager import load_party
from runs.party_manager import save_party
from tracking import log_game_action

from autofighter.cards import instantiate_card
from autofighter.relics import instantiate_relic
from autofighter.reward_preview import merge_preview_payload


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


def _normalise_reward_type(reward_type: str) -> str:
    """Return the canonical staging bucket for ``reward_type``."""

    normalised = (reward_type or "").strip().lower()
    if normalised == "card":
        return "cards"
    if normalised == "relic":
        return "relics"
    if normalised in {"item", "items"}:
        return "items"
    raise ValueError("unsupported reward type")


async def select_card(run_id: str, card_id: str) -> dict[str, Any]:
    if not card_id:
        raise ValueError("invalid card")
    lock = reward_locks.setdefault(run_id, asyncio.Lock())
    async with lock:
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

        base_preview: dict[str, Any] | None = None
        builder = getattr(card, "build_preview", None)
        if callable(builder):
            raw_preview = builder()
            if isinstance(raw_preview, dict):
                base_preview = raw_preview

        staged_card["preview"] = merge_preview_payload(
            base_preview,
            fallback_effects=getattr(card, "effects", {}),
            summary=about,
            stacks=1,
            previous_stacks=0,
            target="party",
        )

        staging["cards"] = [staged_card]
        state["awaiting_card"] = True
        state["awaiting_next"] = False

        ensure_reward_progression(state)

        await asyncio.to_thread(save_map, run_id, state)

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
            "cards": list(getattr(party, "cards", [])),
            "reward_staging": _serialise_staging(staging),
            "awaiting_card": state.get("awaiting_card", False),
            "awaiting_relic": state.get("awaiting_relic", False),
            "awaiting_loot": state.get("awaiting_loot", False),
            "awaiting_next": state.get("awaiting_next", False),
            "reward_progression": (
                dict(state["reward_progression"])
                if isinstance(state.get("reward_progression"), dict)
                else state.get("reward_progression")
            ),
        }

        next_index = current_index + 1
        if isinstance(rooms, list) and 0 <= next_index < len(rooms):
            payload["next_room"] = rooms[next_index].room_type

        return payload


async def select_relic(run_id: str, relic_id: str) -> dict[str, Any]:
    if not relic_id:
        raise ValueError("invalid relic")
    lock = reward_locks.setdefault(run_id, asyncio.Lock())
    async with lock:
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
            "stacks": existing_stacks + 1,
        }
        about = relic.describe(existing_stacks + 1)
        if about:
            staged_relic["about"] = about

        base_preview: dict[str, Any] | None = None
        builder = getattr(relic, "build_preview", None)
        if callable(builder):
            raw_preview = builder(
                stacks=existing_stacks + 1,
                previous_stacks=existing_stacks,
            )
            if isinstance(raw_preview, dict):
                base_preview = raw_preview

        staged_relic["preview"] = merge_preview_payload(
            base_preview,
            fallback_effects=getattr(relic, "effects", {}),
            summary=about,
            stacks=existing_stacks + 1,
            previous_stacks=existing_stacks,
            target="party",
        )

        staging["relics"] = [staged_relic]
        state["awaiting_relic"] = True
        state["awaiting_next"] = False

        ensure_reward_progression(state)

        await asyncio.to_thread(save_map, run_id, state)

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
            "relics": list(getattr(party, "relics", [])),
            "reward_staging": _serialise_staging(staging),
            "awaiting_card": state.get("awaiting_card", False),
            "awaiting_relic": state.get("awaiting_relic", False),
            "awaiting_loot": state.get("awaiting_loot", False),
            "awaiting_next": state.get("awaiting_next", False),
            "reward_progression": (
                dict(state["reward_progression"])
                if isinstance(state.get("reward_progression"), dict)
                else state.get("reward_progression")
            ),
        }

        next_index = current_index + 1
        if isinstance(rooms, list) and 0 <= next_index < len(rooms):
            payload["next_room"] = rooms[next_index].room_type

        return payload


async def acknowledge_loot(run_id: str) -> dict[str, Any]:
    lock = reward_locks.setdefault(run_id, asyncio.Lock())
    async with lock:
        state, rooms = await asyncio.to_thread(load_map, run_id)
        if not state.get("awaiting_loot"):
            raise ValueError("not awaiting loot")
        current_index = int(state.get("current", 0))
        state["awaiting_loot"] = False
        _update_reward_progression(state, completed_step=REWARD_STEP_DROPS)

        if state.get("reward_progression"):
            state["awaiting_next"] = False
        elif not state.get("awaiting_card") and not state.get("awaiting_relic"):
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


def _update_reward_progression(
    state: dict[str, Any],
    *,
    completed_step: str | None = None,
    reopen_step: str | None = None,
) -> None:
    progression, _ = ensure_reward_progression(state)
    if progression is None:
        return

    available: list[str] = list(progression.get("available", []))
    completed: list[str] = list(progression.get("completed", []))

    canonical_completed: list[str] = [
        step for step in available if step in completed
    ]
    completed_set = set(canonical_completed)

    if completed_step:
        normalised = normalise_reward_step(completed_step)
        if normalised and normalised in available:
            completed_set.add(normalised)

    if reopen_step:
        normalised = normalise_reward_step(reopen_step)
        if normalised in completed_set:
            completed_set.remove(normalised)

    canonical_completed = [
        step for step in available if step in completed_set
    ]
    progression["completed"] = canonical_completed

    next_step = None
    for step in available:
        if step not in completed_set:
            next_step = step
            break

    if next_step is None:
        state.pop("reward_progression", None)
        return

    progression["current_step"] = next_step
    state["reward_progression"] = progression


def _refresh_snapshot(run_id: str, state: dict[str, Any], staging: dict[str, Any]) -> None:
    snap = battle_snapshots.get(run_id)
    if not isinstance(snap, dict):
        return

    snapshot = dict(snap)
    ensure_reward_staging(snapshot)
    snapshot["awaiting_card"] = state.get("awaiting_card", False)
    snapshot["awaiting_relic"] = state.get("awaiting_relic", False)
    snapshot["awaiting_loot"] = state.get("awaiting_loot", False)
    snapshot["awaiting_next"] = state.get("awaiting_next", False)
    progression_snapshot = state.get("reward_progression")
    if isinstance(progression_snapshot, dict):
        snapshot["reward_progression"] = dict(progression_snapshot)
    else:
        snapshot.pop("reward_progression", None)

    activation_log = state.get("reward_activation_log")
    if isinstance(activation_log, list):
        snapshot["reward_activation_log"] = [dict(entry) for entry in activation_log if isinstance(entry, dict)]
    else:
        snapshot.pop("reward_activation_log", None)

    snapshot_staging = snapshot.get("reward_staging")
    if isinstance(snapshot_staging, dict):
        snapshot_staging.update(_serialise_staging(staging))
    else:
        snapshot["reward_staging"] = _serialise_staging(staging)
    battle_snapshots[run_id] = snapshot


async def _persist_reward_state(
    run_id: str,
    state: dict[str, Any],
    party,
) -> None:
    await asyncio.to_thread(save_map, run_id, state)
    await asyncio.to_thread(save_party, run_id, party)


async def confirm_reward(run_id: str, reward_type: str) -> dict[str, Any]:
    bucket = _normalise_reward_type(reward_type)

    lock = reward_locks.setdefault(run_id, asyncio.Lock())
    async with lock:
        state, rooms = await asyncio.to_thread(load_map, run_id)
        staging, _ = ensure_reward_staging(state)
        staged_values = staging.get(bucket, [])
        if not staged_values:
            raise ValueError("no staged reward to confirm")

        party = await asyncio.to_thread(load_party, run_id)

        activation_snapshot: list[dict[str, Any]] = []
        if bucket == "cards":
            staged_card = staged_values[0]
            card_id = staged_card.get("id") if isinstance(staged_card, dict) else None
            if not card_id:
                raise ValueError("invalid staged card")
            if card_id not in getattr(party, "cards", []):
                party.cards.append(card_id)
            activation_snapshot = [dict(staged_card)] if isinstance(staged_card, dict) else []
            state["awaiting_card"] = False
            _update_reward_progression(state, completed_step=REWARD_STEP_CARDS)
        elif bucket == "relics":
            staged_relic = staged_values[0]
            relic_id = staged_relic.get("id") if isinstance(staged_relic, dict) else None
            if not relic_id:
                raise ValueError("invalid staged relic")
            party.relics.append(relic_id)
            activation_snapshot = [dict(staged_relic)] if isinstance(staged_relic, dict) else []
            state["awaiting_relic"] = False
            _update_reward_progression(state, completed_step=REWARD_STEP_RELICS)
        elif bucket == "items":
            staged_items = [item for item in staged_values if isinstance(item, dict)]
            inventory = getattr(party, "items", None)
            if isinstance(inventory, list):
                inventory.extend(staged_items)
            else:
                setattr(party, "items", staged_items)
            activation_snapshot = [dict(item) for item in staged_items]
            state["awaiting_loot"] = False
            _update_reward_progression(state, completed_step=REWARD_STEP_DROPS)

        if not isinstance(staging := state.get("reward_staging"), dict):
            staging, _ = ensure_reward_staging(state)

        staging[bucket] = []

        if not (
            state.get("awaiting_card")
            or state.get("awaiting_relic")
            or state.get("awaiting_loot")
        ):
            state["awaiting_next"] = True
        else:
            state["awaiting_next"] = False

        activation_log = state.get("reward_activation_log")
        if not isinstance(activation_log, list):
            activation_log = []
            state["reward_activation_log"] = activation_log

        activation_record = {
            "activation_id": str(uuid4()),
            "bucket": bucket,
            "activated_at": datetime.now(timezone.utc).isoformat(),
            "staged_values": activation_snapshot,
        }
        activation_log.append(activation_record)
        # Keep only the latest 20 entries to bound growth.
        if len(activation_log) > 20:
            del activation_log[:-20]

        await _persist_reward_state(run_id, state, party)
        _refresh_snapshot(run_id, state, staging)

        next_room = None
        if state.get("awaiting_next"):
            next_index = state.get("current", 0) + 1
            if isinstance(rooms, list) and 0 <= next_index < len(rooms):
                next_room = rooms[next_index].room_type

        try:
            await log_game_action(
                f"confirm_{reward_type}",
                run_id=run_id,
                room_id=str(state.get("current", "")),
                details={"bucket": bucket, "activation_id": activation_record["activation_id"]},
            )
        except Exception:
            pass

        payload: dict[str, Any] = {
            "reward_staging": _serialise_staging(staging),
            "awaiting_card": state.get("awaiting_card", False),
            "awaiting_relic": state.get("awaiting_relic", False),
            "awaiting_loot": state.get("awaiting_loot", False),
            "awaiting_next": state.get("awaiting_next", False),
            "activation_record": activation_record,
        }
        if bucket == "cards":
            payload["cards"] = list(getattr(party, "cards", []))
        if bucket == "relics":
            payload["relics"] = list(getattr(party, "relics", []))
        progression_payload = state.get("reward_progression")
        if isinstance(progression_payload, dict):
            payload["reward_progression"] = dict(progression_payload)
        if next_room is not None:
            payload["next_room"] = next_room
        payload["reward_activation_log"] = [dict(entry) for entry in activation_log]
        return payload


async def cancel_reward(run_id: str, reward_type: str) -> dict[str, Any]:
    bucket = _normalise_reward_type(reward_type)

    lock = reward_locks.setdefault(run_id, asyncio.Lock())
    async with lock:
        state, _ = await asyncio.to_thread(load_map, run_id)
        staging, _ = ensure_reward_staging(state)
        staged_values = staging.get(bucket, [])
        if not staged_values:
            raise ValueError("no staged reward to cancel")

        staging[bucket] = []

        if bucket == "cards":
            state["awaiting_card"] = True
            _update_reward_progression(state, reopen_step=REWARD_STEP_CARDS)
        elif bucket == "relics":
            state["awaiting_relic"] = True
            _update_reward_progression(state, reopen_step=REWARD_STEP_RELICS)
        elif bucket == "items":
            state["awaiting_loot"] = True
            _update_reward_progression(state, reopen_step=REWARD_STEP_DROPS)

        if not isinstance(staging := state.get("reward_staging"), dict):
            staging, _ = ensure_reward_staging(state)

        state["awaiting_next"] = False

        party = await asyncio.to_thread(load_party, run_id)
        await _persist_reward_state(run_id, state, party)
        _refresh_snapshot(run_id, state, staging)

        try:
            await log_game_action(
                f"cancel_{reward_type}",
                run_id=run_id,
                room_id=str(state.get("current", "")),
                details={"bucket": bucket},
            )
        except Exception:
            pass

        payload: dict[str, Any] = {
            "reward_staging": _serialise_staging(staging),
            "awaiting_card": state.get("awaiting_card", False),
            "awaiting_relic": state.get("awaiting_relic", False),
            "awaiting_loot": state.get("awaiting_loot", False),
            "awaiting_next": state.get("awaiting_next", False),
        }
        progression_payload = state.get("reward_progression")
        if isinstance(progression_payload, dict):
            payload["reward_progression"] = dict(progression_payload)
        return payload
