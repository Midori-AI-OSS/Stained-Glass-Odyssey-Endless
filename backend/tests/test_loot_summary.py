import pytest

from autofighter.mapgen import MapNode
from autofighter.party import Party
import autofighter.rooms.battle as rooms_module
from autofighter.stats import Stats
from plugins.damage_types import ALL_DAMAGE_TYPES


@pytest.mark.asyncio
async def test_battle_returns_loot_summary(monkeypatch):
    node = MapNode(
        room_id=1, room_type="battle-normal", floor=1, index=1, loop=1, pressure=0
    )
    room = rooms_module.BattleRoom(node)
    member = Stats()
    member.id = "p1"
    party = Party(members=[member])
    monkeypatch.setattr(rooms_module.random, "random", lambda: 0.5)
    monkeypatch.setattr(rooms_module.random, "choice", lambda seq: seq[0])
    monkeypatch.setattr(rooms_module, "card_choices", lambda *a, **k: [])
    result = await room.resolve(party, {})
    assert "loot" in result
    loot = result["loot"]
    assert set(loot).issuperset({"gold", "card_choices", "relic_choices", "items"})
    assert loot["gold"] > 0
    upgrades = [i for i in loot["items"] if i["id"] != "ticket"]
    assert upgrades
    valid_ids = {e.lower() for e in ALL_DAMAGE_TYPES}
    for item in upgrades:
        assert item["id"] in valid_ids
        assert 1 <= item["stars"] <= 4


@pytest.mark.asyncio
async def test_floor_boss_high_star_items(monkeypatch):
    node = MapNode(
        room_id=1, room_type="battle-boss-floor", floor=1, index=1, loop=1, pressure=0
    )
    room = rooms_module.BattleRoom(node)
    member = Stats()
    member.id = "p1"
    party = Party(members=[member])
    monkeypatch.setattr(rooms_module.random, "random", lambda: 0.5)
    monkeypatch.setattr(rooms_module.random, "choice", lambda seq: seq[0])
    monkeypatch.setattr(rooms_module, "card_choices", lambda *a, **k: [])
    result = await room.resolve(party, {})
    stars = [i["stars"] for i in result["loot"]["items"] if i["id"] != "ticket"]
    assert stars and stars[0] >= 3
