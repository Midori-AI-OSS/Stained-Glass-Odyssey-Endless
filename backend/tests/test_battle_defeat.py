import importlib.util
import json
from pathlib import Path

import pytest
from runs.lifecycle import battle_locks

from autofighter.mapgen import MapNode
from autofighter.party import Party
from autofighter.rooms import BattleRoom
from autofighter.stats import Stats
from plugins.characters.player import Player


@pytest.mark.asyncio
async def test_battle_resolve_reports_defeat():
    player = Player()
    player.hp = 0
    party = Party(members=[player])
    node = MapNode(0, "battle-normal", 1, 0, 1, 0)
    room = BattleRoom(node=node)
    foe = Stats()
    foe.id = "dummy"
    result = await room.resolve(party, {}, foe=foe)
    assert result["result"] == "defeat"
    assert result["ended"] is True


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
    return app_module, db_path


@pytest.mark.asyncio
async def test_run_battle_handles_defeat_cleanup(app_with_db, monkeypatch):
    app_module, _ = app_with_db
    app = app_module.app
    client = app.test_client()

    async def fake_resolve(self, party, data, progress, foe=None, **_):
        return {"result": "defeat", "ended": True}

    monkeypatch.setattr(BattleRoom, "resolve", fake_resolve)

    start_resp = await client.post("/run/start", json={"party": ["player"]})
    run_id = (await start_resp.get_json())["run_id"]

    # Start battle via UI action endpoint
    battle_resp = await client.post("/ui/action", json={
        "action": "room_action",
        "params": {
            "room_id": "0",
            "type": "battle",
            "action_type": "start"
        }
    })
    assert battle_resp.status_code == 200

    # Wait for battle task to complete
    task = app_module.battle_tasks[run_id]
    await task

    with app_module.get_save_manager().connection() as conn:
        row = conn.execute("SELECT map FROM runs WHERE id = ?", (run_id,)).fetchone()
    assert row is not None

    state = json.loads(row[0])
    assert state.get("ended") is True
    assert state.get("run_result") == "defeat"
    assert state.get("run_result_logged") in {True, False}

    assert run_id in app_module.battle_snapshots
    snap = app_module.battle_snapshots[run_id]
    assert snap.get("result") == "defeat"
    assert snap.get("ended") is True
    assert run_id not in battle_locks

    ui_resp = await client.get("/ui")
    assert ui_resp.status_code == 200
    ui_state = await ui_resp.get_json()
    assert ui_state.get("active_run") == run_id
    assert ui_state.get("game_state", {}).get("map", {}).get("ended") is True

    shutdown_resp = await client.delete(f"/run/{run_id}")
    assert shutdown_resp.status_code in {200, 207}

    with app_module.get_save_manager().connection() as conn:
        row = conn.execute("SELECT id FROM runs WHERE id = ?", (run_id,)).fetchone()
    assert row is None
    assert run_id not in app_module.battle_snapshots
    assert run_id not in battle_locks
