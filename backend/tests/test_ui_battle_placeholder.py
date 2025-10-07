from __future__ import annotations

import asyncio

import pytest
from runs.lifecycle import battle_snapshots
from runs.lifecycle import battle_tasks
from runs.lifecycle import load_map
from runs.lifecycle import save_map
from test_app import app_with_db as _app_with_db  # noqa: F401

app_with_db = _app_with_db


BATTLE_ROOM_TYPES = {
    "battle-weak",
    "battle-normal",
    "battle-prime",
    "battle-glitched",
    "battle-boss-floor",
}


@pytest.mark.asyncio
async def test_ui_reports_battle_mode_when_snapshot_missing(app_with_db):
    app, _ = app_with_db
    client = app.test_client()

    start_resp = await client.post("/run/start", json={"party": ["player"]})
    assert start_resp.status_code == 200
    run_id = (await start_resp.get_json())["run_id"]

    state, rooms = await asyncio.to_thread(load_map, run_id)
    current_index = int(state.get("current", 0))
    assert rooms
    current_room = rooms[current_index]
    assert current_room.room_type in BATTLE_ROOM_TYPES

    state["awaiting_next"] = False
    state["awaiting_card"] = False
    state["awaiting_relic"] = False
    state["awaiting_loot"] = False
    state["battle"] = True
    state.pop("reward_progression", None)
    await asyncio.to_thread(save_map, run_id, state)

    battle_snapshots.pop(run_id, None)
    battle_tasks.pop(run_id, None)

    resp = await client.get("/ui")
    assert resp.status_code == 200
    payload = await resp.get_json()

    assert payload["mode"] == "battle"
    current_state = payload["game_state"]["current_state"]
    room_data = current_state["room_data"]
    assert room_data is not None
    assert room_data["result"] == "battle"
    assert room_data["snapshot_missing"] is True
    assert room_data["current_index"] == current_index
    assert room_data["current_room"] == current_room.room_type
    assert room_data.get("tags") == list(getattr(current_room, "tags", ()) or [])
