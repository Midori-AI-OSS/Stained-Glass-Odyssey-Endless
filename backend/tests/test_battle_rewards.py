import importlib.util
from pathlib import Path

import pytest

from autofighter.rooms import BattleRoom


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
    return app_module


@pytest.mark.asyncio
async def test_battle_rewards_victory(app_with_db, monkeypatch):
    app_module = app_with_db
    app = app_module.app
    client = app.test_client()

    async def fake_resolve(self, party, data, progress, foe=None):
        return {
            "result": "battle",
            "party": [],
            "gold": party.gold,
            "relics": party.relics,
            "cards": party.cards,
            "card_choices": [],
            "relic_choices": [],
            "loot": {"gold": 1, "items": []},
            "foes": [],
            "room_number": 1,
            "exp_reward": 0,
            "enrage": {"active": False, "stacks": 0},
            "rdr": party.rdr,
        }

    monkeypatch.setattr(BattleRoom, "resolve", fake_resolve)

    start_resp = await client.post("/run/start", json={"party": ["player"]})
    run_id = (await start_resp.get_json())["run_id"]
    await client.put(f"/party/{run_id}", json={"party": ["player"]})

    await client.post(f"/rooms/{run_id}/battle")
    task = app_module.battle_tasks[run_id]
    await task

    snap = app_module.battle_snapshots[run_id]
    assert "loot" in snap
    assert snap.get("awaiting_next") or snap.get("next_room") is not None


@pytest.mark.asyncio
async def test_battle_rewards_defeat(app_with_db, monkeypatch):
    app_module = app_with_db
    app = app_module.app
    client = app.test_client()

    async def fake_resolve(self, party, data, progress, foe=None):
        return {
            "result": "defeat",
            "party": [],
            "gold": party.gold,
            "relics": party.relics,
            "cards": party.cards,
            "card_choices": [],
            "relic_choices": [],
            "loot": {"gold": 0, "items": []},
            "foes": [],
            "room_number": 1,
            "exp_reward": 0,
            "enrage": {"active": False, "stacks": 0},
            "rdr": party.rdr,
            "ended": True,
        }

    monkeypatch.setattr(BattleRoom, "resolve", fake_resolve)

    start_resp = await client.post("/run/start", json={"party": ["player"]})
    run_id = (await start_resp.get_json())["run_id"]

    await client.post(f"/rooms/{run_id}/battle")
    task = app_module.battle_tasks[run_id]
    await task

    snap = app_module.battle_snapshots[run_id]
    assert "loot" in snap
    assert snap.get("ended") is True
    assert snap.get("awaiting_next") is False
    assert snap.get("next_room") is None
