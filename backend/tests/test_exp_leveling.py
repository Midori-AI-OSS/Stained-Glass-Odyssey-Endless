import random

import pytest

from autofighter.mapgen import MapNode
from autofighter.party import Party
from autofighter.rooms.battle.core import BattleRoom
from autofighter.stats import Stats
from plugins.characters.foe_base import FoeBase
from plugins.characters import player as player_mod


@pytest.mark.asyncio
async def test_battle_room_awards_exp(monkeypatch):
    node = MapNode(room_id=0, room_type="battle", floor=1, index=2, loop=1, pressure=0)
    room = BattleRoom(node)
    player = player_mod.Player()
    player.set_base_stat('atk', 1000)
    player.exp = 0
    party = Party(members=[player])

    class DummyFoe(FoeBase):
        id = "dummy"
        name = "Dummy"

    foe = DummyFoe()
    foe.hp = 1
    foe.level = 3
    monkeypatch.setattr(
        "autofighter.rooms.battle.setup._build_foes",
        lambda node, party, **kwargs: [foe],
    )
    monkeypatch.setattr("autofighter.rooms.utils._scale_stats", lambda *args, **kwargs: None)
    result = await room.resolve(party, {})
    assert party.members[0].level == 3
    assert party.members[0].exp == 160
    assert result["room_number"] == 2
    assert result["exp_reward"] == 3 * 12 + 5 * 2


@pytest.mark.asyncio
async def test_level_up_persists_hp(monkeypatch):
    node = MapNode(room_id=0, room_type="battle", floor=1, index=2, loop=1, pressure=0)
    room = BattleRoom(node)
    player = player_mod.Player()
    player.set_base_stat('atk', 1000)
    player.hp = 500
    party = Party(members=[player])

    class DummyFoe(FoeBase):
        id = "dummy"
        name = "Dummy"

    foe = DummyFoe()
    foe.hp = 1
    foe.level = 3
    monkeypatch.setattr(
        "autofighter.rooms.battle.setup._build_foes",
        lambda node, party, **kwargs: [foe],
    )
    monkeypatch.setattr("autofighter.rooms.utils._scale_stats", lambda *args, **kwargs: None)
    await room.resolve(party, {})
    assert party.members[0].level > 1
    assert party.members[0].hp == 500


def test_gain_exp_and_level_up(monkeypatch):
    stats = Stats(hp=100)
    stats.set_base_stat('max_hp', 100)
    stats.set_base_stat('atk', 10)
    stats.set_base_stat('defense', 5)
    monkeypatch.setattr(random, "uniform", lambda a, b: 0)
    stats.gain_exp(100)
    assert stats.level == 4
    assert stats.exp == 300
    assert stats.max_hp == 190
    assert stats.atk == 55
    assert stats.defense == 32
