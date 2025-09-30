import pytest  # noqa: F401
from runs.lifecycle import battle_snapshots
import sqlcipher3
from test_app import app_with_db as _app_with_db  # noqa: F401

app_with_db = _app_with_db


@pytest.mark.asyncio
async def test_ui_end_run_defaults_to_active_run(app_with_db):
    app, db_path = app_with_db
    client = app.test_client()

    start_resp = await client.post("/run/start", json={"party": ["player"]})
    start_data = await start_resp.get_json()
    run_id = start_data["run_id"]

    battle_snapshots[run_id] = {"dummy": True}

    resp = await client.post("/ui/action", json={"action": "end_run"})
    assert resp.status_code == 200
    data = await resp.get_json()
    assert data == {"message": "Run ended successfully"}

    conn = sqlcipher3.connect(db_path)
    try:
        conn.execute("PRAGMA key = 'testkey'")
        cur = conn.execute("SELECT 1 FROM runs WHERE id = ?", (run_id,))
        assert cur.fetchone() is None
    finally:
        conn.close()

    assert run_id not in battle_snapshots


@pytest.mark.asyncio
async def test_ui_end_run_missing_run_returns_404(app_with_db):
    app, _ = app_with_db
    client = app.test_client()

    resp = await client.post(
        "/ui/action",
        json={"action": "end_run", "params": {"run_id": "does-not-exist"}},
    )
    assert resp.status_code == 404
    data = await resp.get_json()
    assert data == {"error": "Run not found"}


@pytest.mark.asyncio
async def test_ui_end_run_without_active_run_returns_400(app_with_db):
    app, _ = app_with_db
    client = app.test_client()

    resp = await client.post("/ui/action", json={"action": "end_run"})
    assert resp.status_code == 400
    data = await resp.get_json()
    assert data["error"] == "No active run"
    assert data["status"] == "error"
