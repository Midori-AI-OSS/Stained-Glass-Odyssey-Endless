import asyncio
import importlib.util
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from game import battle_snapshots
from game import battle_tasks
from game import load_map
from game import save_map
from services.room_service import battle_room
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
async def test_missing_snapshot_restarts_battle(app_module):
    run_info = await start_run(["player"])
    run_id = run_info["run_id"]

    state, rooms = await asyncio.to_thread(load_map, run_id)
    state["awaiting_card"] = True
    await asyncio.to_thread(save_map, run_id, state)

    assert run_id not in battle_snapshots
    assert run_id not in battle_tasks

    snap = await battle_room(run_id, {})
    assert snap["result"] == "battle"
    assert run_id in battle_snapshots
    assert run_id in battle_tasks
