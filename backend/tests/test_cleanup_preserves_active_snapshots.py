import asyncio
import importlib.util
from pathlib import Path

from game import battle_locks
from game import battle_snapshots
from game import battle_tasks
from game import cleanup_battle_state
from game import load_map
from game import save_map
import pytest
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
async def test_cleanup_preserves_snapshot_for_pending_rewards(app_module):
    run_info = await start_run(["player"])
    run_id = run_info["run_id"]

    state, _ = await asyncio.to_thread(load_map, run_id)
    state.update(
        {
            "awaiting_card": True,
            "awaiting_relic": False,
            "awaiting_loot": False,
            "awaiting_next": False,
        }
    )
    await asyncio.to_thread(save_map, run_id, state)

    battle_snapshots[run_id] = {"result": "victory", "awaiting_card": True}
    battle_locks[run_id] = asyncio.Lock()

    task = asyncio.create_task(asyncio.sleep(0))
    battle_tasks[run_id] = task
    await task

    await cleanup_battle_state()

    assert run_id not in battle_tasks
    assert run_id in battle_snapshots
    assert run_id in battle_locks
