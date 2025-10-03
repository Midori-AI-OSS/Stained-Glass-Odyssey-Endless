from __future__ import annotations

import asyncio
import json
from pathlib import Path
import sys

import pytest


@pytest.mark.asyncio
async def test_prune_runs_on_startup_clears_persistent_and_cached_state(monkeypatch, tmp_path):
    db_path = tmp_path / "save.db"
    monkeypatch.setenv("AF_DB_PATH", str(db_path))
    monkeypatch.setenv("AF_DB_KEY", "testkey")
    monkeypatch.setenv("AF_TRACK_DB_PATH", str(tmp_path / "track.db"))
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]))

    sys.modules.pop("tracking", None)

    # Ensure the save manager will pick up the new database path.
    from runs import encryption
    from runs import lifecycle
    from tracking import manager as tracking_manager

    tracking_manager.TRACKING_MANAGER = None

    encryption.SAVE_MANAGER = None
    encryption.FERNET = None

    lifecycle.purge_all_run_state()

    from services import run_service

    start_result = await run_service.start_run(["player"])
    run_id = start_result["run_id"]

    lifecycle.battle_snapshots[run_id] = {"awaiting_next": False}
    lifecycle.battle_locks[run_id] = asyncio.Lock()
    lifecycle.battle_tasks[run_id] = asyncio.create_task(asyncio.sleep(10))

    with encryption.get_save_manager().connection() as conn:
        remaining = conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
    assert remaining == 1

    await run_service.prune_runs_on_startup()
    await asyncio.sleep(0)

    with encryption.get_save_manager().connection() as conn:
        remaining = conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
    assert remaining == 0

    assert lifecycle.battle_tasks == {}
    assert lifecycle.battle_snapshots == {}
    assert lifecycle.battle_locks == {}

    tracking_db = tracking_manager.get_tracking_manager()
    with tracking_db.connection() as conn:
        outcome_row = conn.execute(
            "SELECT outcome FROM runs WHERE run_id = ?",
            (run_id,),
        ).fetchone()
        assert outcome_row is not None
        assert outcome_row[0] == "aborted"

        session_row = conn.execute(
            "SELECT logout_ts FROM play_sessions WHERE session_id = ?",
            (run_id,),
        ).fetchone()
        assert session_row is not None
        assert session_row[0] is not None

        menu_row = conn.execute(
            "SELECT menu_item, result, details_json FROM menu_actions WHERE result = ?",
            ("startup_pruned",),
        ).fetchone()
        assert menu_row is not None
        assert menu_row[0] == "Run"
        assert menu_row[1] == "startup_pruned"
        details = json.loads(menu_row[2])
        assert details["run_id"] == run_id
        assert details["reason"] == "startup_prune"

    # A second invocation should be a no-op and should not raise errors.
    await run_service.prune_runs_on_startup()
    await asyncio.sleep(0)
