import asyncio
import importlib.util
import math
from pathlib import Path
import random

import pytest
from runs.lifecycle import load_map
from runs.party_manager import load_party
from runs.party_manager import save_party
from services.room_service import shop_room
from services.run_service import advance_room
from services.run_service import start_run

from autofighter.mapgen import MapGenerator
from autofighter.mapgen import MapNode
from autofighter.party import Party
from autofighter.rooms.shop import PRICE_BY_STARS
from autofighter.rooms.shop import REROLL_COST
from autofighter.rooms.shop import ShopRoom
from autofighter.rooms.shop import _taxed_price
from plugins.characters._base import PlayerBase


@pytest.mark.asyncio
async def test_shop_generate_buy_reroll():
    random.seed(0)
    node = MapNode(room_id=1, room_type="shop", floor=1, index=1, loop=1, pressure=0)
    room = ShopRoom(node)

    p1 = PlayerBase()
    p1.id = "p1"
    p1.set_base_stat('max_hp', 200)
    p1.hp = 50

    p2 = PlayerBase()
    p2.id = "p2"
    p2.set_base_stat('max_hp', 600)
    p2.hp = 100

    p3 = PlayerBase()
    p3.id = "p3"
    p3.set_base_stat('max_hp', 50)
    p3.hp = 25

    p4 = PlayerBase()
    p4.id = "p4"
    p4.set_base_stat('max_hp', 150)
    p4.hp = 150

    initial_gold = 250
    party = Party(members=[p1, p2, p3, p4], gold=initial_gold)

    first = await room.resolve(party, {"action": ""})
    assert [m.hp for m in party.members] == [100, 150, 50, 150]
    assert first["stock"]
    initial_stock = first["stock"].copy()

    purchase = initial_stock[0]
    second = await room.resolve(party, purchase)
    assert len(second["stock"]) == len(initial_stock) - 1
    assert party.gold == initial_gold - purchase["cost"]
    if purchase["type"] == "card":
        assert purchase["id"] in party.cards
    else:
        assert purchase["id"] in party.relics

    third = await room.resolve(party, {"action": "reroll"})
    assert party.gold == initial_gold - purchase["cost"] - REROLL_COST
    assert third["stock"]
    assert third["stock"] != second["stock"]


@pytest.mark.asyncio
async def test_shop_cost_scales_with_pressure():
    random.seed(0)
    pressure = 3
    node = MapNode(room_id=1, room_type="shop", floor=1, index=1, loop=1, pressure=pressure)
    room = ShopRoom(node)

    p = PlayerBase()
    p.id = "p"
    p.set_base_stat('max_hp', 100)
    p.hp = 100

    party = Party(members=[p], gold=5000)

    first = await room.resolve(party, {"action": ""})
    assert first["stock"]
    for item in first["stock"]:
        base = PRICE_BY_STARS[item["stars"]]
        min_cost = int(base * (1.26 ** pressure) * 0.95)
        max_cost = int(base * (1.26 ** pressure) * 1.05)
        assert min_cost <= item["base_price"] <= max_cost
        assert item["cost"] >= item["base_price"]
        assert item["tax"] == item["cost"] - item["base_price"]


@pytest.mark.asyncio
async def test_shop_tax_scales_and_persists():
    base_entry = {
        "id": "test_card_1",
        "name": "Test Card",
        "stars": 1,
        "type": "card",
        "base_price": 100,
        "price": 100,
        "cost": 100,
        "tax": 0,
    }

    node_low = MapNode(room_id=5, room_type="shop", floor=1, index=1, loop=1, pressure=0)
    node_low.stock = [dict(base_entry), {**base_entry, "id": "test_card_2"}]
    room_low = ShopRoom(node_low)

    member = PlayerBase()
    member.id = "tester"
    member.set_base_stat('max_hp', 100)
    member.hp = 50
    party_low = Party(members=[member], gold=500)

    first_low = await room_low.resolve(party_low, {})
    assert first_low["items_bought"] == 0
    assert first_low["stock"][0]["tax"] == 0

    purchase = first_low["stock"][0]
    second_low = await room_low.resolve(party_low, {"id": purchase["id"], "cost": purchase["cost"]})
    assert second_low["items_bought"] == 1

    revisit_low = await room_low.resolve(party_low, {})
    assert revisit_low["items_bought"] == 1
    assert revisit_low["stock"]
    low_item = revisit_low["stock"][0]
    expected_low_tax = math.ceil(
        low_item["base_price"] * 0.01 * (node_low.pressure + 1) * revisit_low["items_bought"]
    )
    assert low_item["tax"] == expected_low_tax
    assert low_item["cost"] == low_item["base_price"] + expected_low_tax

    node_high = MapNode(room_id=6, room_type="shop", floor=1, index=2, loop=1, pressure=4)
    node_high.items_bought = revisit_low["items_bought"]
    node_high.stock = [dict(base_entry)]
    room_high = ShopRoom(node_high)

    member_high = PlayerBase()
    member_high.id = "tester_high"
    member_high.set_base_stat('max_hp', 100)
    member_high.hp = 50
    party_high = Party(members=[member_high], gold=500)

    high_view = await room_high.resolve(party_high, {})
    assert high_view["items_bought"] == revisit_low["items_bought"]
    high_item = high_view["stock"][0]
    expected_high_tax = math.ceil(
        high_item["base_price"] * 0.01 * (node_high.pressure + 1) * high_view["items_bought"]
    )
    assert high_item["tax"] == expected_high_tax
    assert expected_high_tax > expected_low_tax


@pytest.mark.asyncio
async def test_shop_handles_multi_item_payload():
    node = MapNode(room_id=9, room_type="shop", floor=1, index=1, loop=1, pressure=2)
    node.stock = [
        {
            "id": "multi_card",
            "name": "Multi Card",
            "stars": 1,
            "type": "card",
            "base_price": 100,
            "price": 100,
            "cost": 100,
            "tax": 0,
        },
        {
            "id": "multi_relic",
            "name": "Multi Relic",
            "stars": 2,
            "type": "relic",
            "base_price": 200,
            "price": 200,
            "cost": 200,
            "tax": 0,
        },
        {
            "id": "multi_card_two",
            "name": "Multi Card Two",
            "stars": 1,
            "type": "card",
            "base_price": 100,
            "price": 100,
            "cost": 100,
            "tax": 0,
        },
    ]
    room = ShopRoom(node)

    member = PlayerBase()
    member.id = "multi"
    member.set_base_stat('max_hp', 100)
    member.hp = 90
    party = Party(members=[member], gold=1000)

    initial_view = await room.resolve(party, {})
    assert initial_view["items_bought"] == 0
    assert len(initial_view["stock"]) == 3

    first_entry = initial_view["stock"][0]
    second_entry = initial_view["stock"][1]
    third_entry = initial_view["stock"][2]

    first_cost = _taxed_price(
        first_entry["base_price"],
        node.pressure,
        initial_view["items_bought"],
        None,
    )
    second_cost = _taxed_price(
        second_entry["base_price"],
        node.pressure,
        initial_view["items_bought"] + 1,
        None,
    )

    result = await room.resolve(
        party,
        {
            "items": [
                {"id": first_entry["id"], "cost": first_cost},
                {"id": second_entry["id"], "cost": second_cost},
            ],
        },
    )

    assert result["items_bought"] == 2
    assert len(result["stock"]) == 1

    assert party.gold == 1000 - first_cost - second_cost
    assert first_entry["id"] in party.cards
    assert second_entry["id"] in party.relics

    remaining = result["stock"][0]
    expected_remaining_cost = _taxed_price(
        remaining["base_price"],
        node.pressure,
        result["items_bought"],
        None,
    )
    assert remaining["cost"] == expected_remaining_cost
    assert remaining["tax"] == expected_remaining_cost - remaining["base_price"]
    assert remaining["id"] == third_entry["id"]


@pytest.mark.asyncio
async def test_shop_accepts_single_item_dict_payload():
    node = MapNode(room_id=11, room_type="shop", floor=1, index=1, loop=1, pressure=0)
    node.stock = [
        {
            "id": "single_dict_card",
            "name": "Single Dict Card",
            "stars": 1,
            "type": "card",
            "base_price": 100,
            "price": 100,
            "cost": 100,
            "tax": 0,
        }
    ]
    room = ShopRoom(node)

    member = PlayerBase()
    member.id = "single"
    member.set_base_stat('max_hp', 100)
    member.hp = 70
    party = Party(members=[member], gold=200)

    initial_view = await room.resolve(party, {})
    assert len(initial_view["stock"]) == 1

    entry = initial_view["stock"][0]
    expected_cost = _taxed_price(
        entry["base_price"],
        node.pressure,
        initial_view["items_bought"],
        None,
    )

    result = await room.resolve(
        party,
        {"items": {"id": entry["id"], "cost": expected_cost}},
    )

    assert result["items_bought"] == 1
    assert not result["stock"]
    assert party.gold == 200 - expected_cost
    assert entry["id"] in party.cards


@pytest.mark.asyncio
async def test_shop_multi_item_payload_skips_invalid_entries():
    node = MapNode(room_id=10, room_type="shop", floor=1, index=1, loop=1, pressure=1)
    node.stock = [
        {
            "id": "invalid_card",
            "name": "Invalid Card",
            "stars": 1,
            "type": "card",
            "base_price": 100,
            "price": 100,
            "cost": 100,
            "tax": 0,
        },
        {
            "id": "valid_relic",
            "name": "Valid Relic",
            "stars": 2,
            "type": "relic",
            "base_price": 200,
            "price": 200,
            "cost": 200,
            "tax": 0,
        },
    ]
    room = ShopRoom(node)

    member = PlayerBase()
    member.id = "skip"
    member.set_base_stat('max_hp', 100)
    member.hp = 80
    party = Party(members=[member], gold=600)

    initial_view = await room.resolve(party, {})
    initial_gold = party.gold
    first_entry = initial_view["stock"][0]
    second_entry = initial_view["stock"][1]

    wrong_cost = first_entry["cost"] + 50
    valid_cost = _taxed_price(
        second_entry["base_price"],
        node.pressure,
        initial_view["items_bought"],
        None,
    )

    result = await room.resolve(
        party,
        {
            "items": [
                {"id": first_entry["id"], "cost": wrong_cost},
                {"id": second_entry["id"], "cost": valid_cost},
            ],
        },
    )

    assert result["items_bought"] == 1
    assert party.gold == initial_gold - valid_cost
    assert second_entry["id"] in party.relics
    assert any(entry["id"] == first_entry["id"] for entry in result["stock"])

    remaining_entry = next(entry for entry in result["stock"] if entry["id"] == first_entry["id"])
    expected_cost = _taxed_price(
        remaining_entry["base_price"],
        node.pressure,
        result["items_bought"],
        None,
    )
    assert remaining_entry["cost"] == expected_cost
    assert remaining_entry["tax"] == expected_cost - remaining_entry["base_price"]


@pytest.fixture()
def app_with_shop(tmp_path, monkeypatch):
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

    def fake_generate_floor(self, *args, **kwargs):
        return [
            MapNode(0, "start", 1, 0, 1, 0),
            MapNode(1, "shop", 1, 1, 1, 0),
            MapNode(2, "battle-weak", 1, 2, 1, 0),
        ]

    monkeypatch.setattr(MapGenerator, "generate_floor", fake_generate_floor)
    return app_module.app, db_path


@pytest.mark.asyncio
async def test_shop_allows_multiple_actions(app_with_shop):
    _, _ = app_with_shop
    start = await start_run(["player"])
    run_id = start["run_id"]

    party = await asyncio.to_thread(load_party, run_id)
    party.gold = 300
    await asyncio.to_thread(save_party, run_id, party)

    async def resolve_shop(params: dict | None = None):
        payload = params or {}
        result = await shop_room(run_id, payload)
        assert result["result"] == "shop"
        return result

    data = await resolve_shop()
    assert data["stock"]
    gold = data["gold"]

    item1 = data["stock"][0]
    data = await resolve_shop({"id": item1["id"], "cost": item1["cost"]})
    spent = item1["cost"]
    assert data["gold"] == gold - spent

    data = await resolve_shop({"action": "reroll"})
    spent += REROLL_COST
    assert data["gold"] == gold - spent

    item2 = data["stock"][0]
    data = await resolve_shop({"id": item2["id"], "cost": item2["cost"]})
    spent += item2["cost"]
    assert data["gold"] == gold - spent

    data = await resolve_shop({"action": "reroll"})
    spent += REROLL_COST
    assert data["gold"] == gold - spent

    state, _ = await asyncio.to_thread(load_map, run_id)
    assert not state.get("awaiting_next")

    leave_data = await resolve_shop({"action": "leave"})
    assert "next_room" in leave_data

    state, _ = await asyncio.to_thread(load_map, run_id)
    assert state.get("awaiting_next")

    final = await advance_room(run_id)
    assert isinstance(final.get("current_index"), int)
