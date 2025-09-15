import asyncio
import importlib.util
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runs.lifecycle import battle_snapshots
from runs.lifecycle import battle_tasks
from runs.lifecycle import load_map
from runs.lifecycle import save_map
from services.room_service import battle_room
from services.run_service import start_run


@pytest.fixture()
def app_module(tmp_path, monkeypatch):
    db_path = tmp_path / "save.db"
    monkeypatch.setenv("AF_DB_PATH", str(db_path))
    monkeypatch.setenv("AF_DB_KEY", "testkey")
    monkeypatch.syspath_prepend(Path(__file__).resolve().parents[1])
    spec = importlib.util.spec_from_file_location(
        "app", Path(__file__).resolve().parents[1] / "app.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.mark.asyncio
async def test_battle_room_awaiting_next_returns_snapshot(app_module):
    run_info = await start_run(["player"])
    run_id = run_info["run_id"]

    state, rooms = await asyncio.to_thread(load_map, run_id)
    state["awaiting_next"] = True
    await asyncio.to_thread(save_map, run_id, state)

    battle_snapshots[run_id] = {"result": "battle", "awaiting_next": True}

    assert run_id not in battle_tasks

    snap1 = await battle_room(run_id, {})
    assert snap1 is battle_snapshots[run_id]
    assert run_id not in battle_tasks

    snap2 = await battle_room(run_id, {})
    assert snap2 is snap1
    assert run_id not in battle_tasks
