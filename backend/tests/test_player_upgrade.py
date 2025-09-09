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
    conn = sqlcipher3.connect(db_path)
    conn.execute("PRAGMA key = 'testkey'")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS damage_types (id TEXT PRIMARY KEY, type TEXT)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS upgrade_items (id TEXT PRIMARY KEY, count INTEGER NOT NULL)"
    )
    conn.execute(
        "INSERT OR REPLACE INTO damage_types (id, type) VALUES (?, ?)",
        ("player", "fire"),
    )
    conn.execute(
        "INSERT OR REPLACE INTO upgrade_items (id, count) VALUES (?, ?)",
        ("fire_4", 20),
    )
    conn.commit()
    conn.close()
    return app_module.app, db_path


@pytest.mark.asyncio
async def test_upgrade_requires_json_data(app_with_db):
    app, db_path = app_with_db
    client = app.test_client()

    # Test that API now requires JSON data
    resp = await client.post("/players/player/upgrade")
    data = await resp.get_json()
    assert resp.status_code == 400
    assert "JSON data required" in data["error"]
