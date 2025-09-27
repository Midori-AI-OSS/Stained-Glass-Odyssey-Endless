from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import importlib
import json

import pytest
from quart import Quart
import sqlcipher3

importlib.invalidate_caches()
sys.modules.pop("services", None)
sys.modules.pop("tracking", None)
sys.modules.pop("battle_logging", None)
sys.modules.pop("battle_logging.writers", None)
from routes.ui import bp as ui_bp


@pytest.fixture()
def app_with_db(tmp_path, monkeypatch):
    db_path = tmp_path / "save.db"
    monkeypatch.setenv("AF_DB_PATH", str(db_path))
    monkeypatch.setenv("AF_DB_KEY", "testkey")
    monkeypatch.setenv("UV_EXTRA", "test")

    app = Quart(__name__)
    app.register_blueprint(ui_bp)
    app.testing = True
    return app, db_path


@pytest.mark.asyncio
async def test_update_party_success(app_with_db):
    app, db_path = app_with_db
    client = app.test_client()

    start_resp = await client.post("/run/start", json={"party": ["player"]})
    assert start_resp.status_code == 200

    conn = sqlcipher3.connect(db_path)
    conn.execute("PRAGMA key = 'testkey'")
    conn.execute("CREATE TABLE IF NOT EXISTS owned_players (id TEXT PRIMARY KEY)")
    conn.execute("INSERT OR IGNORE INTO owned_players (id) VALUES (?)", ("ally",))
    conn.commit()

    resp = await client.post(
        "/ui/action",
        json={"action": "update_party", "params": {"party": ["player", "ally"]}},
    )
    assert resp.status_code == 200
    data = await resp.get_json()
    assert data["party"]["members"] == ["player", "ally"]

    cur = conn.execute("SELECT party FROM runs")
    row = cur.fetchone()
    assert row is not None
    party_state = json.loads(row[0])
    assert party_state["members"] == ["player", "ally"]
    assert set(party_state["exp"]) == {"player", "ally"}
    assert set(party_state["level"]) == {"player", "ally"}


@pytest.mark.asyncio
async def test_update_party_missing_run(app_with_db):
    app, _ = app_with_db
    client = app.test_client()

    resp = await client.post(
        "/ui/action",
        json={
            "action": "update_party",
            "params": {"run_id": "missing", "party": ["player"]},
        },
    )
    assert resp.status_code == 404
    data = await resp.get_json()
    assert data["error"] == "Run not found"


@pytest.mark.asyncio
async def test_update_party_invalid_members(app_with_db):
    app, _ = app_with_db
    client = app.test_client()

    start_resp = await client.post("/run/start", json={"party": ["player"]})
    assert start_resp.status_code == 200

    duplicate_resp = await client.post(
        "/ui/action",
        json={
            "action": "update_party",
            "params": {"party": ["player", "player"]},
        },
    )
    assert duplicate_resp.status_code == 400
    duplicate_data = await duplicate_resp.get_json()
    assert duplicate_data["error"] == "invalid party"

    unowned_resp = await client.post(
        "/ui/action",
        json={
            "action": "update_party",
            "params": {"party": ["player", "becca"]},
        },
    )
    assert unowned_resp.status_code == 400
    unowned_data = await unowned_resp.get_json()
    assert unowned_data["error"] == "unowned character"
