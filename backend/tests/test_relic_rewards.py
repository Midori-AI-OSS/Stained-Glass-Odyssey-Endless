import pytest

from autofighter.mapgen import MapNode
from autofighter.party import Party
import autofighter.rooms.battle.core as rooms_module
from autofighter.stats import Stats
from plugins.relics.threadbare_cloak import ThreadbareCloak


@pytest.mark.asyncio
async def test_battle_offers_relic_choices(monkeypatch):
    node = MapNode(room_id=1, room_type="battle-normal", floor=1, index=1, loop=1, pressure=0)
    room = rooms_module.BattleRoom(node)
    member = Stats()
    member.id = "p1"
    party = Party(members=[member])
    monkeypatch.setattr(rooms_module, "card_choices", lambda *args, **kwargs: [])
    monkeypatch.setattr(rooms_module.random, "random", lambda: 0.0)
    result = await room.resolve(party, {})
    assert len(result["relic_choices"]) == 3


@pytest.mark.asyncio
async def test_relic_choice_includes_about_and_stacks(monkeypatch):
    node = MapNode(room_id=1, room_type="battle-normal", floor=1, index=1, loop=1, pressure=0)
    room = rooms_module.BattleRoom(node)
    member = Stats()
    member.id = "p1"
    party = Party(members=[member])
    party.relics.append("threadbare_cloak")
    monkeypatch.setattr(rooms_module, "card_choices", lambda *a, **k: [])
    monkeypatch.setattr(rooms_module, "relic_choices", lambda *a, **k: [ThreadbareCloak()])
    monkeypatch.setattr(rooms_module.random, "random", lambda: 0.0)
    result = await room.resolve(party, {})
    relic = result["relic_choices"][0]
    assert relic["stacks"] == 1
    assert "6%" in relic["about"]
