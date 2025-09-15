import asyncio
import importlib.util
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runs.lifecycle import battle_snapshots
from runs.lifecycle import load_map
from runs.lifecycle import save_map
from services.room_service import battle_room
from services.room_service import boss_room
from services.run_service import start_run


@pytest.fixture()
def app_module(tmp_path, monkeypatch):
    db_path = tmp_path / "save.db"
    monkeypatch.setenv("AF_DB_PATH", str(db_path))
    monkeypatch.setenv("AF_DB_KEY", "testkey")
    spec = importlib.util.spec_from_file_location(
        "app", Path(__file__).resolve().parents[1] / "app.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.mark.asyncio
async def test_battle_snapshot_reload_starts_battle(app_module):
    run_info = await start_run(["player"])
    run_id = run_info["run_id"]
    assert run_id not in battle_snapshots

    snap = await battle_room(run_id, {"action": "snapshot"})
    assert snap["result"] == "battle"
    assert run_id in battle_snapshots


@pytest.mark.asyncio
async def test_boss_snapshot_reload_starts_battle(app_module):
    run_info = await start_run(["player"])
    run_id = run_info["run_id"]

    state, rooms = await asyncio.to_thread(load_map, run_id)
    state["rooms"][state["current"]]["room_type"] = "battle-boss-floor"
    await asyncio.to_thread(save_map, run_id, state)

    assert run_id not in battle_snapshots

    snap = await boss_room(run_id, {"action": "snapshot"})
    assert snap["result"] == "boss"
    assert run_id in battle_snapshots
