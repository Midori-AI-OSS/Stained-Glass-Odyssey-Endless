"""Helpers for managing run and battle state."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable
from collections.abc import Callable
import gc
import json
import logging
from typing import Any

from battle_logging.writers import end_run_logging

from autofighter.gacha import GachaManager
from autofighter.mapgen import MapNode
from autofighter.party import Party
from autofighter.rooms import BattleRoom
from autofighter.stats import Stats

from .encryption import get_save_manager
from .party_manager import save_party

log = logging.getLogger(__name__)

battle_tasks: dict[str, asyncio.Task] = {}
battle_snapshots: dict[str, dict[str, Any]] = {}
battle_locks: dict[str, asyncio.Lock] = {}

RECENT_FOE_COOLDOWN = 3


def sanitize_recent_foes(raw: Any) -> list[dict[str, int]]:
    """Return a normalized list of active foe cooldown entries."""

    entries: list[dict[str, int]] = []
    if not isinstance(raw, list):
        return entries
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        foe_id = entry.get("id")
        cooldown = entry.get("cooldown")
        try:
            cooldown_int = int(cooldown)
        except (TypeError, ValueError):
            continue
        if not foe_id or cooldown_int <= 0:
            continue
        entries.append({"id": str(foe_id), "cooldown": cooldown_int})
    return entries


async def cleanup_battle_state() -> None:
    """Remove completed battle tasks and associated state."""

    completed = [run_id for run_id, task in battle_tasks.items() if task.done()]

    tasks_removed = 0
    snapshots_removed = 0
    locks_removed = 0

    for run_id in completed:
        if battle_tasks.pop(run_id, None) is not None:
            tasks_removed += 1

        snap = battle_snapshots.get(run_id, {})
        awaiting_next = snap.get("awaiting_next")
        awaiting_card = snap.get("awaiting_card")
        awaiting_relic = snap.get("awaiting_relic")
        awaiting_loot = snap.get("awaiting_loot")
        ended = snap.get("ended")

        if None in {
            awaiting_next,
            awaiting_card,
            awaiting_relic,
            awaiting_loot,
            ended,
        }:
            try:
                state, _ = await asyncio.to_thread(load_map, run_id)
            except Exception:
                state = {}
            awaiting_next = state.get("awaiting_next", False)
            awaiting_card = state.get("awaiting_card", False)
            awaiting_relic = state.get("awaiting_relic", False)
            awaiting_loot = state.get("awaiting_loot", False)
            ended = state.get("ended", False)

        has_rewards = any([awaiting_card, awaiting_relic, awaiting_loot])

        if ended or (not awaiting_next and not has_rewards):
            if battle_snapshots.pop(run_id, None) is not None:
                snapshots_removed += 1
            if battle_locks.pop(run_id, None) is not None:
                locks_removed += 1

    removed_total = tasks_removed + snapshots_removed + locks_removed
    if removed_total:
        message = (
            "Removed %d tasks, %d snapshots, %d locks",
            tasks_removed,
            snapshots_removed,
            locks_removed,
        )
        if removed_total > 10:
            log.warning(*message)
        else:
            log.info(*message)

    gc.collect()


def get_battle_state_sizes() -> dict[str, int]:
    """Return the current sizes of battle state dictionaries."""

    return {
        "tasks": len(battle_tasks),
        "snapshots": len(battle_snapshots),
        "locks": len(battle_locks),
    }


def load_map(run_id: str) -> tuple[dict, list[MapNode]]:
    with get_save_manager().connection() as conn:
        cur = conn.execute("SELECT map FROM runs WHERE id = ?", (run_id,))
        row = cur.fetchone()
    if row is None:
        return {"rooms": [], "current": 0, "battle": False}, []
    state = json.loads(row[0])
    rooms = [MapNode.from_dict(n) for n in state.get("rooms", [])]
    return state, rooms


def save_map(run_id: str, state: dict) -> None:
    with get_save_manager().connection() as conn:
        conn.execute(
            "UPDATE runs SET map = ? WHERE id = ?",
            (json.dumps(state), run_id),
        )


async def _run_battle(
    run_id: str,
    room: BattleRoom,
    foes: Stats | list[Stats],
    party: Party,
    data: dict[str, Any],
    state: dict[str, Any],
    rooms: list[MapNode],
    progress: Callable[[dict[str, Any]], Awaitable[None]],
) -> None:
    try:
        try:
            result = await room.resolve(party, data, progress, foes, run_id=run_id)
        except Exception as exc:
            state["battle"] = False
            log.exception("Battle resolution failed for %s", run_id)
            if run_id not in battle_snapshots:
                battle_snapshots[run_id] = {
                    "result": "error",
                    "error": str(exc),
                    "ended": True,
                    "party": [],
                    "foes": [],
                    "awaiting_next": False,
                    "awaiting_card": False,
                    "awaiting_relic": False,
                    "awaiting_loot": False,
                }
            try:
                await asyncio.to_thread(save_map, run_id, state)
                await asyncio.to_thread(save_party, run_id, party)
            except Exception:
                pass
            from app import request_shutdown

            await request_shutdown()
            return
        state["battle"] = False
        try:
            loot_items = result.get("loot", {}).get("items", [])
            manager = GachaManager(get_save_manager())
            items = manager._get_items()
            for entry in loot_items:
                if entry.get("id") == "ticket":
                    items["ticket"] = items.get("ticket", 0) + 1
                else:
                    key = f"{entry['id']}_{entry['stars']}"
                    items[key] = items.get(key, 0) + 1
            manager._auto_craft(items)
            manager._set_items(items)
            result["items"] = items
            if result.get("result") == "defeat":
                state["awaiting_card"] = False
                state["awaiting_relic"] = False
                state["awaiting_loot"] = False
                state["awaiting_next"] = False
                try:
                    await asyncio.to_thread(save_map, run_id, state)
                    await asyncio.to_thread(save_party, run_id, party)
                    result.update(
                        {
                            "run_id": run_id,
                            "current_room": rooms[state["current"]].room_type,
                            "current_index": state["current"],
                            "awaiting_card": False,
                            "awaiting_relic": False,
                            "awaiting_loot": False,
                            "awaiting_next": False,
                            "next_room": None,
                            "ended": True,
                        }
                    )
                    battle_snapshots[run_id] = result
                finally:
                    try:
                        # End run logging when run is deleted due to defeat
                        end_run_logging()
                        with get_save_manager().connection() as conn:
                            conn.execute("DELETE FROM runs WHERE id = ?", (run_id,))
                    except Exception:
                        pass
                return
            has_card_choices = bool(result.get("card_choices"))
            has_relic_choices = bool(result.get("relic_choices"))
            # Check if there's loot to review (gold or items)
            has_loot = bool(result.get("loot", {}).get("gold", 0) > 0 or
                           len(result.get("loot", {}).get("items", [])) > 0)

            # Set up reward progression sequence for proper UI flow
            if has_card_choices or has_relic_choices or has_loot:
                progression = {
                    "available": [],
                    "completed": [],
                    "current_step": None
                }

                # Build sequence of steps based on what rewards are available
                if has_card_choices:
                    progression["available"].append("card")
                if has_relic_choices:
                    progression["available"].append("relic")
                if has_loot:
                    progression["available"].append("loot")

                # If there are no actual reward choices, allow immediate advancement
                if not (has_card_choices or has_relic_choices or has_loot):
                    # No rewards at all, ready to advance immediately
                    state["awaiting_card"] = False
                    state["awaiting_relic"] = False
                    state["awaiting_loot"] = False
                    state["awaiting_next"] = True
                    next_type = (
                        rooms[state["current"] + 1].room_type
                        if state["current"] + 1 < len(rooms)
                        else None
                    )
                else:
                    # Start with first available step
                    progression["current_step"] = progression["available"][0]

                    state["reward_progression"] = progression
                    state["awaiting_card"] = has_card_choices
                    state["awaiting_relic"] = has_relic_choices
                    state["awaiting_loot"] = has_loot
                    state["awaiting_next"] = False
                    next_type = None
            else:
                # No rewards at all, ready to advance immediately
                state["awaiting_card"] = False
                state["awaiting_relic"] = False
                state["awaiting_loot"] = False
                state["awaiting_next"] = True
                next_type = (
                    rooms[state["current"] + 1].room_type
                    if state["current"] + 1 < len(rooms)
                    else None
                )
            existing_recent = sanitize_recent_foes(state.get("recent_foes"))
            updated_recent: dict[str, int] = {}
            for entry in existing_recent:
                new_cooldown = entry["cooldown"] - 1
                if new_cooldown > 0:
                    updated_recent[entry["id"]] = max(
                        updated_recent.get(entry["id"], 0), new_cooldown
                    )

            foe_ids: list[str] = []
            for foe_info in result.get("foes", []):
                if isinstance(foe_info, dict):
                    foe_id = foe_info.get("id")
                    if foe_id:
                        foe_ids.append(str(foe_id))

            if not foe_ids:
                foe_list = foes if isinstance(foes, list) else [foes]
                for foe_obj in foe_list:
                    foe_id = getattr(foe_obj, "id", None)
                    if foe_id:
                        foe_ids.append(str(foe_id))

            for foe_id in foe_ids:
                updated_recent[foe_id] = RECENT_FOE_COOLDOWN

            state["recent_foes"] = [
                {"id": foe_id, "cooldown": cooldown}
                for foe_id, cooldown in sorted(
                    updated_recent.items(), key=lambda item: (-item[1], item[0])
                )
            ]

            await asyncio.to_thread(save_map, run_id, state)
            await asyncio.to_thread(save_party, run_id, party)
            result.update(
                {
                    "run_id": run_id,
                    "action": data.get("action", ""),
                    "next_room": next_type,
                    "current_room": rooms[state["current"]].room_type,
                    "current_index": state["current"],
                    "awaiting_card": state.get("awaiting_card", False),
                    "awaiting_relic": state.get("awaiting_relic", False),
                    "awaiting_loot": state.get("awaiting_loot", False),
                    "awaiting_next": state.get("awaiting_next", False),
                }
            )
            battle_snapshots[run_id] = result
        except Exception as exc:
            log.exception("Battle processing failed for %s", run_id)
            battle_snapshots[run_id] = {
                "result": "error",
                "loot": result.get("loot"),
                "error": str(exc),
                "ended": True,
                "party": [],
                "foes": [],
                "awaiting_next": False,
                "awaiting_card": False,
                "awaiting_relic": False,
                "awaiting_loot": False,
            }
    finally:
        battle_tasks.pop(run_id, None)


__all__ = [
    "cleanup_battle_state",
    "get_battle_state_sizes",
    "load_map",
    "save_map",
    "battle_tasks",
    "battle_snapshots",
    "battle_locks",
    "sanitize_recent_foes",
    "_run_battle",
]
