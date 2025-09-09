import pytest

from autofighter.mapgen import MapNode
from autofighter.party import Party
import autofighter.rooms.battle as rooms_module
from autofighter.stats import Stats
from plugins.damage_types import ALL_DAMAGE_TYPES


@pytest.mark.asyncio
async def test_rdr_scales_relic_drop(monkeypatch):
    node = MapNode(
        room_id=1, room_type="battle-normal", floor=1, index=1, loop=1, pressure=0
    )
    room = rooms_module.BattleRoom(node)
    member = Stats()
    member.id = "p1"
    low = Party(members=[member], rdr=1.0)
    high = Party(members=[member], rdr=3.0)
    monkeypatch.setattr(rooms_module, "card_choices", lambda *a, **k: [])
    monkeypatch.setattr(
        rooms_module,
        "relic_choices",
        lambda *a, **k: [
            type("R", (), {"id": "r", "name": "R", "stars": k.get("stars", 1)})()
            for _ in range(3)
        ],
    )
    monkeypatch.setattr(rooms_module.random, "random", lambda: 0.2)
    result_low = await room.resolve(low, {})
    result_high = await room.resolve(high, {})
    assert result_low["relic_choices"] == []
    assert len(result_high["relic_choices"]) == 3


@pytest.mark.asyncio
async def test_rdr_scales_items_and_tickets(monkeypatch):
    node = MapNode(
        room_id=1, room_type="battle-normal", floor=1, index=1, loop=1, pressure=0
    )
    room = rooms_module.BattleRoom(node)
    member = Stats()
    member.id = "p1"
    low = Party(members=[member], rdr=1.0)
    high = Party(members=[member], rdr=2.0)
    monkeypatch.setattr(rooms_module, "card_choices", lambda *a, **k: [])
    monkeypatch.setattr(rooms_module, "relic_choices", lambda *a, **k: [])
    monkeypatch.setattr(rooms_module.random, "choice", lambda seq: seq[0])
    monkeypatch.setattr(rooms_module.random, "random", lambda: 0.15)
    result_low = await room.resolve(low, {})
    result_high = await room.resolve(high, {})
    low_upgrades = [i for i in result_low["loot"]["items"] if i["id"] != "ticket"]
    high_upgrades = [i for i in result_high["loot"]["items"] if i["id"] != "ticket"]
    assert len(high_upgrades) > len(low_upgrades)
    assert {i["stars"] for i in low_upgrades} == {i["stars"] for i in high_upgrades}
    low_tickets = [i for i in result_low["loot"]["items"] if i["id"] == "ticket"]
    high_tickets = [i for i in result_high["loot"]["items"] if i["id"] == "ticket"]
    assert len(high_tickets) > len(low_tickets)


@pytest.mark.asyncio
async def test_low_rdr_still_drops_item(monkeypatch):
    node = MapNode(
        room_id=1, room_type="battle-normal", floor=1, index=1, loop=1, pressure=0
    )
    room = rooms_module.BattleRoom(node)
    member = Stats()
    member.id = "p1"
    party = Party(members=[member], rdr=0.5)
    monkeypatch.setattr(rooms_module, "card_choices", lambda *a, **k: [])
    monkeypatch.setattr(rooms_module, "relic_choices", lambda *a, **k: [])
    monkeypatch.setattr(rooms_module.random, "choice", lambda seq: seq[0])
    monkeypatch.setattr(rooms_module.random, "random", lambda: 0.99)
    result = await room.resolve(party, {})
    upgrades = [i for i in result["loot"]["items"] if i["id"] != "ticket"]
    assert len(upgrades) == 1
    valid_ids = {e.lower() for e in ALL_DAMAGE_TYPES}
    assert upgrades[0]["id"] in valid_ids


@pytest.mark.asyncio
async def test_rdr_buffs_relic_star_odds(monkeypatch):
    node = MapNode(
        room_id=1, room_type="battle-normal", floor=1, index=1, loop=1, pressure=0
    )
    room = rooms_module.BattleRoom(node)
    member = Stats()
    member.id = "p1"
    low = Party(members=[member], rdr=1.0)
    high = Party(members=[member], rdr=10.0)
    monkeypatch.setattr(rooms_module, "card_choices", lambda *a, **k: [])
    monkeypatch.setattr(rooms_module, "_pick_relic_stars", lambda room: 3)
    monkeypatch.setattr(rooms_module, "_roll_relic_drop", lambda *a, **k: True)
    monkeypatch.setattr(
        rooms_module,
        "relic_choices",
        lambda *a, **k: [
            type("R", (), {"id": "r", "name": "R", "stars": k.get("stars", 1)})()
        ],
    )
    monkeypatch.setattr(rooms_module.random, "random", lambda: 0.0)
    result_low = await room.resolve(low, {})
    result_high_lucky = await room.resolve(high, {})
    monkeypatch.setattr(rooms_module.random, "random", lambda: 0.99)
    result_high_unlucky = await room.resolve(high, {})
    assert result_low["relic_choices"][0]["stars"] == 3
    assert result_high_lucky["relic_choices"][0]["stars"] == 4
    assert result_high_unlucky["relic_choices"][0]["stars"] == 3


@pytest.mark.asyncio
async def test_rdr_buffs_card_star_odds(monkeypatch):
    node = MapNode(
        room_id=1, room_type="battle-boss-floor", floor=1, index=1, loop=1, pressure=0
    )
    room = rooms_module.BossRoom(node)
    member = Stats()
    member.id = "p1"
    low = Party(members=[member], rdr=1.0)
    high = Party(members=[member], rdr=10.0)
    monkeypatch.setattr(rooms_module, "_pick_card_stars", lambda room: 3)
    monkeypatch.setattr(rooms_module, "_roll_relic_drop", lambda *a, **k: False)
    monkeypatch.setattr(
        rooms_module,
        "card_choices",
        lambda party, stars: [
            type("C", (), {"id": "c", "name": "C", "stars": stars})()
        ],
    )
    monkeypatch.setattr(rooms_module.random, "random", lambda: 0.0)
    result_low = await room.resolve(low, {})
    result_high_lucky = await room.resolve(high, {})
    monkeypatch.setattr(rooms_module.random, "random", lambda: 0.99)
    result_high_unlucky = await room.resolve(high, {})
    assert result_low["card_choices"][0]["stars"] == 3
    assert result_high_lucky["card_choices"][0]["stars"] == 4
    assert result_high_unlucky["card_choices"][0]["stars"] == 3


@pytest.mark.asyncio
async def test_rdr_scales_floor_boss_items_same_star(monkeypatch):
    node = MapNode(
        room_id=1, room_type="battle-boss-floor", floor=1, index=1, loop=1, pressure=0
    )
    room = rooms_module.BattleRoom(node)
    member = Stats()
    member.id = "p1"
    low = Party(members=[member], rdr=1.0)
    high = Party(members=[member], rdr=3.0)
    monkeypatch.setattr(rooms_module, "card_choices", lambda *a, **k: [])
    monkeypatch.setattr(rooms_module, "relic_choices", lambda *a, **k: [])
    monkeypatch.setattr(rooms_module.random, "choice", lambda seq: seq[0])
    monkeypatch.setattr(rooms_module.random, "random", lambda: 0.9)
    result_low = await room.resolve(low, {})
    result_high = await room.resolve(high, {})
    low_upgrades = [i for i in result_low["loot"]["items"] if i["id"] != "ticket"]
    high_upgrades = [i for i in result_high["loot"]["items"] if i["id"] != "ticket"]
    assert len(high_upgrades) > len(low_upgrades)
    assert (
        {i["stars"] for i in low_upgrades} == {i["stars"] for i in high_upgrades} == {3}
    )
