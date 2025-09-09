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
async def test_damage_type_persists(app_with_db):
    app, db_path = app_with_db
    client = app.test_client()

    resp1 = await client.get("/players")
    data1 = await resp1.get_json()
    becca1 = next(p for p in data1["players"] if p["id"] == "becca")

    resp2 = await client.get("/players")
    data2 = await resp2.get_json()
    becca2 = next(p for p in data2["players"] if p["id"] == "becca")

    assert becca1["element"] == becca2["element"]

    conn = sqlcipher3.connect(db_path)
    conn.execute("PRAGMA key = 'testkey'")
    cur = conn.execute("SELECT type FROM damage_types WHERE id = ?", ("becca",))
    row = cur.fetchone()
    assert row is not None
    assert row[0] == becca1["element"]
    conn.close()
