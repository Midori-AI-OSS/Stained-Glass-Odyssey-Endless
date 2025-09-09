import asyncio
import importlib.util
from pathlib import Path

import pytest

import autofighter.rooms.battle as rooms_module


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
async def test_battle_loot_items_update_inventory(app_with_db, monkeypatch):
    app, app_module = app_with_db
    client = app.test_client()

    start_resp = await client.post("/run/start", json={"party": ["player"]})
    run_id = (await start_resp.get_json())["run_id"]
    await client.put(f"/party/{run_id}", json={"party": ["player"]})

    async def fake_resolve(self, party, data, progress, foe):
        loot = {
            "gold": 0,
            "card_choices": [],
            "relic_choices": [],
            "items": [
                {"id": "fire", "stars": 1},
                {"id": "ticket", "stars": 0},
            ],
        }
        return {
            "result": "battle",
            "party": [],
            "gold": party.gold,
            "relics": party.relics,
            "cards": party.cards,
            "card_choices": [],
            "relic_choices": [],
            "loot": loot,
            "foes": [],
            "room_number": 1,
            "exp_reward": 0,
            "enrage": {"active": False, "stacks": 0},
            "rdr": party.rdr,
        }

    monkeypatch.setattr(rooms_module.BattleRoom, "resolve", fake_resolve)

    await client.post(f"/rooms/{run_id}/battle")

    for _ in range(20):
        snap_resp = await client.post(
            f"/rooms/{run_id}/battle", json={"action": "snapshot"}
        )
        data = await snap_resp.get_json()
        if "loot" in data:
            break
        await asyncio.sleep(0.1)
    else:
        pytest.fail("battle did not complete")

    loot_items = data["loot"]["items"]
    assert loot_items

    manager = app_module.GachaManager(app_module.get_save_manager())
    items = manager._get_items()

    expected: dict[str, int] = {}
    for entry in loot_items:
        if entry["id"] == "ticket":
            key = "ticket"
        else:
            key = f"{entry['id']}_{entry['stars']}"
        expected[key] = expected.get(key, 0) + 1
    for key, count in expected.items():
        assert items.get(key) == count
    assert data["items"] == items
