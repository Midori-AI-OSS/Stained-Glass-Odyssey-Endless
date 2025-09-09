import base64
import hashlib
import importlib.util
import json
from pathlib import Path

from cryptography.fernet import Fernet
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
async def test_backup_restore_and_wipe(app_with_db):
    app, db_path = app_with_db
    client = app.test_client()

    resp = await client.post("/run/start", json={"party": ["player"]})
    run_id = (await resp.get_json())["run_id"]

    original_mtime = db_path.stat().st_mtime

    backup = await client.get("/save/backup")
    token = await backup.get_data()
    key = base64.urlsafe_b64encode(hashlib.sha256(b"testkey").digest())
    fernet = Fernet(key)
    package = fernet.decrypt(token)
    obj = json.loads(package)

    tampered = json.dumps({"hash": obj["hash"], "data": obj["data"] + "x"}).encode()
    bad_token = fernet.encrypt(tampered)
    bad = await client.post("/save/restore", data=bad_token)
    assert bad.status_code == 400

    await client.delete(f"/run/{run_id}")
    wipe = await client.post("/save/wipe")
    assert wipe.status_code == 200
    assert db_path.stat().st_mtime > original_mtime

    conn = sqlcipher3.connect(db_path)
    conn.execute("PRAGMA key = 'testkey'")
    assert conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0] == 0

    good = await client.post("/save/restore", data=token)
    assert good.status_code == 200
    assert conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0] == 1
    conn.close()


@pytest.mark.asyncio
async def test_wipe_allows_new_run(app_with_db):
    app, _ = app_with_db
    client = app.test_client()

    resp = await client.post("/run/start", json={"party": ["player"]})
    run_id = (await resp.get_json())["run_id"]
    await client.delete(f"/run/{run_id}")
    await client.post("/save/wipe")

    fresh = await client.post("/run/start", json={"party": ["player"]})
    assert fresh.status_code == 200
    data = await fresh.get_json()
    assert "run_id" in data


@pytest.mark.asyncio
async def test_wipe_seeds_random_persona(app_with_db):
    app, db_path = app_with_db
    client = app.test_client()

    await client.post("/save/wipe")

    conn = sqlcipher3.connect(db_path)
    conn.execute("PRAGMA key = 'testkey'")
    rows = {row[0] for row in conn.execute("SELECT id FROM owned_players")}
    conn.close()

    assert rows <= {"player", "lady_darkness", "lady_light"}
    assert len(rows) == 2
