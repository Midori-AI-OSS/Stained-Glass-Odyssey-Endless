import random
import asyncio
import itertools
import importlib.util
from pathlib import Path

import pytest

import autofighter.rooms.battle.core as rooms_module
from autofighter.rooms.battle import resolution as resolution_module


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
                # include a ticket despite the 0.05% × rdr normal-battle drop rate for determinism
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


@pytest.mark.asyncio
async def test_high_rdr_item_rewards_are_bounded(monkeypatch):
    random.seed(1337)

    class DummyRelics:
        def count(self, _):
            return 0

    class DummyParty:
        def __init__(self):
            self.gold = 0
            self.relics = DummyRelics()
            self.cards: list = []
            self.rdr = 0.0

    class DummyNode:
        room_type = "battle"
        index = 1
        loop = 1

    class DummyRoom:
        def __init__(self):
            self.strength = 1.0
            self.node = DummyNode()

    party = DummyParty()
    combat_party = DummyParty()
    room = DummyRoom()

    card_counter = itertools.count()

    class DummyCard:
        def __init__(self, idx: int):
            self.id = f"card-{idx}"
            self.name = self.id
            self.stars = 1
            self.about = "test"

    def fake_card_choices(_, __, count=1):
        idx = next(card_counter)
        return [DummyCard(idx) for _ in range(count)]

    async def fake_emit_async(*_, **__):
        return None

    monkeypatch.setattr(resolution_module, "_pick_card_stars", lambda *_: 1)
    monkeypatch.setattr(resolution_module, "_apply_rdr_to_stars", lambda base, *_: base)
    monkeypatch.setattr(resolution_module, "card_choices", fake_card_choices)
    monkeypatch.setattr(resolution_module, "_roll_relic_drop", lambda *_: False)
    monkeypatch.setattr(resolution_module, "_pick_item_stars", lambda *_: 1)
    monkeypatch.setattr(resolution_module, "_calc_gold", lambda *_: 0)
    monkeypatch.setattr(resolution_module.BUS, "emit_async", fake_emit_async)

    rewards = await resolution_module.resolve_rewards(
        room=room,
        party=party,
        combat_party=combat_party,
        foes=[],
        foes_data=[],
        enrage_payload={"active": False, "stacks": 0},
        start_gold=0,
        temp_rdr=10000.0,
        party_data=[],
        party_summons={},
        foe_summons={},
        action_queue_snapshot={},
        battle_logger=None,
        exp_reward=0,
        run_id=None,
        effects_charge=None,
    )

    loot_items = rewards["loot"]["items"]
    upgrade_items = [item for item in loot_items if item["id"] != "ticket"]

    assert len(upgrade_items) <= 2
    assert upgrade_items[0]["stars"] == 4
    if len(upgrade_items) == 2:
        assert upgrade_items[1]["id"] == upgrade_items[0]["id"]
        assert upgrade_items[1]["stars"] == 1
