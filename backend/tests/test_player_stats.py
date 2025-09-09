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
        "app",
        Path(__file__).resolve().parents[1] / "app.py",
    )
    app_module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(app_module)
    app_module.app.testing = True
    return app_module.app, db_path


@pytest.mark.asyncio
async def test_player_stats_endpoint(app_with_db):
    app, db_path = app_with_db
    conn = sqlcipher3.connect(db_path)
    conn.execute("PRAGMA key = 'testkey'")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS options (key TEXT PRIMARY KEY, value TEXT)"
    )
    conn.execute(
        "INSERT OR REPLACE INTO options (key, value) VALUES (?, ?)",
        ("stat_refresh_rate", "12"),
    )
    conn.commit()
    conn.close()

    client = app.test_client()
    resp = await client.get("/player/stats")
    data = await resp.get_json()
    assert resp.status_code == 200
    assert data["refresh_rate"] == 10
    assert set(data["stats"].keys()) == {
        "core",
        "offense",
        "defense",
        "vitality",
        "advanced",
        "status",
    }
    assert data["stats"]["core"]["hp"] == 1000
    assert data["stats"]["offense"]["atk"] == 100

    conn = sqlcipher3.connect(db_path)
    conn.execute("PRAGMA key = 'testkey'")
    conn.execute(
        "UPDATE options SET value = ? WHERE key = ?", ("0", "stat_refresh_rate")
    )
    conn.commit()
    conn.close()

    resp = await client.get("/player/stats")
    data = await resp.get_json()
    assert data["refresh_rate"] == 1
