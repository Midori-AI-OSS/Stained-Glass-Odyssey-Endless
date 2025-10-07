import importlib.util
from pathlib import Path

import pytest
import sqlcipher3


@pytest.fixture()
def app_with_db(tmp_path, monkeypatch):
    db_path = tmp_path / "save.db"
    monkeypatch.setenv("AF_DB_PATH", str(db_path))
    monkeypatch.setenv("AF_DB_KEY", "testkey")
    monkeypatch.syspath_prepend(Path(__file__).resolve().parents[1])
    spec = importlib.util.spec_from_file_location(
        "app", Path(__file__).resolve().parents[1] / "app.py",
    )
    app_module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(app_module)
    app_module.app.testing = True
    return app_module.app, db_path


@pytest.mark.asyncio
async def test_start_run_with_party(app_with_db):
    app, db_path = app_with_db
    client = app.test_client()

    resp = await client.post(
        "/run/start", json={"party": ["player"], "damage_type": "Ice"}
    )
    assert resp.status_code == 200
    data = await resp.get_json()
    assert data["party"][0]["id"] == "player"

    conn = sqlcipher3.connect(db_path)
    conn.execute("PRAGMA key = 'testkey'")
    cur = conn.execute(
        "SELECT type FROM damage_types WHERE id = ?", ("player",)
    )
    assert cur.fetchone()[0] == "Ice"


@pytest.mark.asyncio
async def test_party_validation(app_with_db):
    app, db_path = app_with_db
    client = app.test_client()

    resp = await client.post("/run/start", json={"party": ["becca"]})
    assert resp.status_code == 400

    resp = await client.post(
        "/run/start", json={"party": ["player", "player"]}
    )
    assert resp.status_code == 400

    resp = await client.post(
        "/run/start", json={"party": ["player", "becca"]}
    )
    assert resp.status_code == 400

    resp = await client.post(
        "/run/start", json={"party": ["player"], "damage_type": "Generic"}
    )
    assert resp.status_code == 400

    conn = sqlcipher3.connect(db_path)
    conn.execute("PRAGMA key = 'testkey'")
    conn.execute("CREATE TABLE IF NOT EXISTS owned_players (id TEXT PRIMARY KEY)")
    extra = [(pid,) for pid in ["ally", "becca", "carly", "graygray"]]
    conn.executemany("INSERT INTO owned_players (id) VALUES (?)", extra)
    resp = await client.post(
        "/run/start",
        json={
            "party": ["player", "luna", "ally", "becca", "carly", "graygray"],
        },
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_players_endpoint_reports_ultimate_cap(app_with_db):
    app, _ = app_with_db
    client = app.test_client()

    resp = await client.get("/players")
    assert resp.status_code == 200
    payload = await resp.get_json()
    luna_entry = next(p for p in payload["players"] if p["id"] == "luna")
    assert luna_entry["stats"]["ultimate_max"] == 15_000
