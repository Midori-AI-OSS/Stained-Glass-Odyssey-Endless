import importlib.util
from pathlib import Path
import random

import pytest

from autofighter.mapgen import MapGenerator
from autofighter.mapgen import MapNode
from autofighter.party import Party
from autofighter.rooms.shop import PRICE_BY_STARS
from autofighter.rooms.shop import REROLL_COST
from autofighter.rooms.shop import ShopRoom
from plugins.players._base import PlayerBase


@pytest.mark.asyncio
async def test_shop_generate_buy_reroll():
    random.seed(0)
    node = MapNode(room_id=1, room_type="shop", floor=1, index=1, loop=1, pressure=0)
    room = ShopRoom(node)

    p1 = PlayerBase()
    p1.id = "p1"
    p1.max_hp = 200
    p1.hp = 50

    p2 = PlayerBase()
    p2.id = "p2"
    p2.max_hp = 600
    p2.hp = 100

    p3 = PlayerBase()
    p3.id = "p3"
    p3.max_hp = 50
    p3.hp = 25

    p4 = PlayerBase()
    p4.id = "p4"
    p4.max_hp = 150
    p4.hp = 150

    party = Party(members=[p1, p2, p3, p4], gold=100)

    first = await room.resolve(party, {"action": ""})
    assert [m.hp for m in party.members] == [100, 150, 50, 150]
    assert first["stock"]
    initial_stock = first["stock"].copy()

    purchase = initial_stock[0]
    second = await room.resolve(party, purchase)
    assert len(second["stock"]) == len(initial_stock) - 1
    assert party.gold == 100 - purchase["cost"]
    if purchase["type"] == "card":
        assert purchase["id"] in party.cards
    else:
        assert purchase["id"] in party.relics

    third = await room.resolve(party, {"action": "reroll"})
    assert party.gold == 100 - purchase["cost"] - REROLL_COST
    assert third["stock"]
    assert third["stock"] != second["stock"]


@pytest.mark.asyncio
async def test_shop_cost_scales_with_pressure():
    random.seed(0)
    pressure = 3
    node = MapNode(
        room_id=1, room_type="shop", floor=1, index=1, loop=1, pressure=pressure
    )
    room = ShopRoom(node)

    p = PlayerBase()
    p.id = "p"
    p.max_hp = 100
    p.hp = 100

    party = Party(members=[p], gold=5000)

    first = await room.resolve(party, {"action": ""})
    assert first["stock"]
    for item in first["stock"]:
        base = PRICE_BY_STARS[item["stars"]]
        min_cost = int(base * (1.26**pressure) * 0.95)
        max_cost = int(base * (1.26**pressure) * 1.05)
        assert min_cost <= item["cost"] <= max_cost


@pytest.fixture()
def app_with_shop(tmp_path, monkeypatch):
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

    def fake_generate_floor(self):
        return [
            MapNode(0, "start", 1, 0, 1, 0),
            MapNode(1, "shop", 1, 1, 1, 0),
            MapNode(2, "battle-weak", 1, 2, 1, 0),
        ]

    monkeypatch.setattr(MapGenerator, "generate_floor", fake_generate_floor)
    return app_module.app, db_path


@pytest.mark.asyncio
async def test_shop_allows_multiple_actions(app_with_shop):
    app, _ = app_with_shop
    client = app.test_client()

    start = await client.post("/run/start", json={"party": ["player"]})
    run_id = (await start.get_json())["run_id"]
    await client.put(
        f"/party/{run_id}",
        json={"party": ["player"], "gold": 300},
    )

    first = await client.post(f"/rooms/{run_id}/shop")
    data = await first.get_json()
    assert data["stock"]
    gold = data["gold"]

    item1 = data["stock"][0]
    buy1 = await client.post(
        f"/rooms/{run_id}/shop", json={"id": item1["id"], "cost": item1["cost"]}
    )
    data = await buy1.get_json()
    spent = item1["cost"]
    assert data["gold"] == gold - spent

    reroll1 = await client.post(f"/rooms/{run_id}/shop", json={"action": "reroll"})
    data = await reroll1.get_json()
    spent += REROLL_COST
    assert data["gold"] == gold - spent

    item2 = data["stock"][0]
    buy2 = await client.post(
        f"/rooms/{run_id}/shop", json={"id": item2["id"], "cost": item2["cost"]}
    )
    data = await buy2.get_json()
    spent += item2["cost"]
    assert data["gold"] == gold - spent

    reroll2 = await client.post(f"/rooms/{run_id}/shop", json={"action": "reroll"})
    data = await reroll2.get_json()
    spent += REROLL_COST
    assert data["gold"] == gold - spent

    next_attempt = await client.post(f"/run/{run_id}/next")
    assert next_attempt.status_code == 400

    leave = await client.post(f"/rooms/{run_id}/shop", json={"action": "leave"})
    leave_data = await leave.get_json()
    assert "next_room" in leave_data

    final = await client.post(f"/run/{run_id}/next")
    assert final.status_code == 200
