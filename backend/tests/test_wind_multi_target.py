import random

import pytest

from autofighter.effects import EffectManager
from autofighter.mapgen import MapNode
from autofighter.party import Party
from autofighter.rooms.battle import BattleRoom
from autofighter.stats import Stats
from plugins.damage_types.wind import Wind


@pytest.mark.asyncio
async def test_wind_player_hits_all_foes(monkeypatch):
    calls = []

    original = EffectManager.maybe_inflict_dot

    def spy(self, attacker, damage, turns=None):
        calls.append(self.stats.id)
        return original(self, attacker, damage, turns)

    monkeypatch.setattr(EffectManager, "maybe_inflict_dot", spy)
    node = MapNode(
        room_id=0,
        room_type="battle-normal",
        floor=1,
        index=1,
        loop=1,
        pressure=0,
    )
    room = BattleRoom(node)
    player = Stats(atk=1000, effect_hit_rate=2.0, damage_type=Wind())
    player.id = "p1"
    foe1 = Stats(hp=3, max_hp=3, defense=0)
    foe1.id = "f1"
    foe2 = Stats(hp=3, max_hp=3, defense=0)
    foe2.id = "f2"
    party = Party(members=[player])
    random.seed(0)
    await room.resolve(party, {}, foe=[foe1, foe2])
    assert "f1" in calls
    assert "f2" in calls


@pytest.mark.asyncio
async def test_wind_foe_hits_all_party_members(monkeypatch):
    calls = []

    original = EffectManager.maybe_inflict_dot

    def spy(self, attacker, damage, turns=None):
        calls.append(self.stats.id)
        return original(self, attacker, damage, turns)

    monkeypatch.setattr(EffectManager, "maybe_inflict_dot", spy)
    node = MapNode(
        room_id=0,
        room_type="battle-normal",
        floor=1,
        index=1,
        loop=1,
        pressure=0,
    )
    room = BattleRoom(node)
    player1 = Stats(
        hp=200,
        max_hp=200,
        atk=0,
        defense=10,
        mitigation=1.0,
        effect_resistance=0.0,
    )
    player1.id = "p1"
    player2 = Stats(
        hp=200,
        max_hp=200,
        atk=1000,
        defense=1,
        mitigation=1.0,
        effect_resistance=0.0,
    )
    player2.id = "p2"
    party = Party(members=[player1, player2])
    foe = Stats(
        hp=3,
        max_hp=3,
        atk=5,
        defense=0,
        damage_type=Wind(),
        effect_hit_rate=2.0,
    )
    foe.id = "f1"
    random.seed(0)
    await room.resolve(party, {}, foe=foe)
    assert "p1" in calls
    assert calls.count("f1") >= 2
