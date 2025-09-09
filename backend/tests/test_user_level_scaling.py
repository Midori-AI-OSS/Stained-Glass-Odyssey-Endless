import importlib.util
from pathlib import Path

import pytest


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
    return app_module.app, app_module


@pytest.mark.asyncio
async def test_party_stats_scaled_by_user_level(app_with_db):
    app, app_module = app_with_db
    client = app.test_client()

    with app_module.get_save_manager().connection() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO options (key, value) VALUES (?, ?)",
            ("user_level", "5"),
        )

    resp = await client.post("/run/start", json={"party": ["player"]})
    run_id = (await resp.get_json())["run_id"]

    party = app_module.load_party(run_id)
    player = next(m for m in party.members if m.id == "player")
    assert (player.max_hp, player.atk, player.defense) == (1050, 105, 52)
