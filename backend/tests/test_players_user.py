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
        "app", Path(__file__).resolve().parents[1] / "app.py",
    )
    app_module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(app_module)
    app_module.app.testing = True
    return app_module.app, db_path


@pytest.mark.asyncio
async def test_players_returns_user(app_with_db):
    app, _ = app_with_db
    client = app.test_client()
    resp = await client.get("/players")
    data = await resp.get_json()
    assert "user" in data
    assert isinstance(data["user"], dict)


@pytest.mark.asyncio
async def test_players_unique_and_matches_playable_roster(app_with_db):
    app, _ = app_with_db
    client = app.test_client()
    resp = await client.get("/players")
    assert resp.status_code == 200
    data = await resp.get_json()
    players = data.get("players", [])
    ids = [player.get("id") for player in players]
    assert len(ids) == len(set(ids)), "Duplicate player ids returned"

    from plugins import characters as player_plugins

    export_names = getattr(
        player_plugins, "_PLAYABLE_EXPORTS", tuple(player_plugins.__all__)
    )
    playable_ids: set[str] = set()
    for name in export_names:
        cls = getattr(player_plugins, name, None)
        if cls is None:
            continue
        if getattr(cls, "plugin_type", "player") != "player":
            continue
        inst = cls()
        playable_ids.add(inst.id)

    assert len(players) == len(playable_ids)

