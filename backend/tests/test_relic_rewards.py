import pytest

from autofighter.mapgen import MapNode
from autofighter.party import Party
from autofighter.rooms import BossRoom
import autofighter.rooms.battle.core as rooms_module
import autofighter.rooms.battle.rewards as rewards_module
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


@pytest.mark.parametrize(
    ("roll", "expected"),
    [
        (0.0, 1),
        (0.989999, 1),
        (0.99, 2),
    ],
)
def test_pick_card_stars_normal_thresholds(monkeypatch, roll, expected):
    node = MapNode(room_id=1, room_type="battle-normal", floor=1, index=1, loop=1, pressure=0)
    room = rooms_module.BattleRoom(node)
    monkeypatch.setattr(rewards_module.random, "random", lambda: roll)
    assert rewards_module._pick_card_stars(room) == expected


@pytest.mark.parametrize(
    ("roll", "expected"),
    [
        (0.0, 1),
        (0.699999, 1),
        (0.70, 2),
        (0.949999, 2),
        (0.95, 3),
        (0.989999, 3),
        (0.99, 4),
        (0.998999, 4),
        (0.999, 5),
    ],
)
def test_pick_card_stars_boosted_thresholds(monkeypatch, roll, expected):
    node = MapNode(room_id=1, room_type="battle-normal", floor=1, index=1, loop=1, pressure=0)
    room = rooms_module.BattleRoom(node)
    room.strength = 1.5
    monkeypatch.setattr(rewards_module.random, "random", lambda: roll)
    assert rewards_module._pick_card_stars(room) == expected


@pytest.mark.parametrize(
    ("roll", "expected"),
    [
        (0.0, 3),
        (0.949999, 3),
        (0.95, 4),
        (0.989999, 4),
        (0.99, 5),
    ],
)
def test_pick_card_stars_boss_thresholds(monkeypatch, roll, expected):
    node = MapNode(room_id=1, room_type="battle-boss-floor", floor=1, index=1, loop=1, pressure=0)
    room = BossRoom(node)
    monkeypatch.setattr(rewards_module.random, "random", lambda: roll)
    assert rewards_module._pick_card_stars(room) == expected


@pytest.mark.parametrize(
    ("roll", "expected"),
    [
        (0.0, 1),
        (0.949999, 1),
        (0.95, 2),
        (0.979999, 2),
        (0.98, 3),
    ],
)
def test_pick_relic_stars_normal_thresholds(monkeypatch, roll, expected):
    node = MapNode(room_id=1, room_type="battle-normal", floor=1, index=1, loop=1, pressure=0)
    room = rooms_module.BattleRoom(node)
    monkeypatch.setattr(rewards_module.random, "random", lambda: roll)
    assert rewards_module._pick_relic_stars(room) == expected


@pytest.mark.parametrize(
    ("roll", "expected"),
    [
        (0.0, 3),
        (0.899999, 3),
        (0.9, 4),
        (0.989999, 4),
        (0.99, 5),
    ],
)
def test_pick_relic_stars_boss_thresholds(monkeypatch, roll, expected):
    node = MapNode(room_id=1, room_type="battle-boss-floor", floor=1, index=1, loop=1, pressure=0)
    room = BossRoom(node)
    monkeypatch.setattr(rewards_module.random, "random", lambda: roll)
    assert rewards_module._pick_relic_stars(room) == expected
