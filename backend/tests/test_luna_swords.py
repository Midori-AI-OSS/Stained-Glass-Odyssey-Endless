import pytest

from autofighter.mapgen import MapNode
from autofighter.party import Party
from autofighter.rooms.battle.setup import setup_battle
from autofighter.stats import BUS
from autofighter.stats import Stats
from autofighter.summons.manager import SummonManager
from plugins.characters.luna import Luna
from plugins.passives.normal.luna_lunar_reservoir import LunaLunarReservoir


@pytest.fixture(autouse=True)
def _reset_luna_state():
    LunaLunarReservoir._charge_points.clear()
    LunaLunarReservoir._swords_by_owner.clear()
    SummonManager.reset_all()
    yield
    LunaLunarReservoir._charge_points.clear()
    LunaLunarReservoir._swords_by_owner.clear()
    SummonManager.reset_all()


def _basic_party() -> Party:
    member = Stats()
    member.id = "hero"
    member.hp = member.max_hp
    return Party(members=[member], gold=0, relics=[], cards=[], rdr=1.0)


def _boss_node() -> MapNode:
    return MapNode(
        room_id=0,
        room_type="battle-boss",
        floor=3,
        index=1,
        loop=1,
        pressure=0,
    )


def _normal_node() -> MapNode:
    return MapNode(
        room_id=0,
        room_type="battle",
        floor=1,
        index=1,
        loop=1,
        pressure=0,
    )


@pytest.mark.asyncio
async def test_luna_boss_spawns_four_swords():
    node = _boss_node()
    party = _basic_party()
    luna = Luna()
    luna.id = "luna_boss"
    luna.rank = "boss"

    await setup_battle(node, party, foe=luna)

    swords = SummonManager.get_summons(luna.id)
    assert len(swords) == 4
    assert all(getattr(sword, "luna_sword", False) for sword in swords)
    assert all(str(getattr(sword, "summon_type", "")).startswith("luna_sword_") for sword in swords)


@pytest.mark.asyncio
async def test_luna_glitched_boss_spawns_nine_swords():
    node = _boss_node()
    party = _basic_party()
    luna = Luna()
    luna.id = "luna_glitched"
    luna.rank = "glitched boss"

    await setup_battle(node, party, foe=luna)

    swords = SummonManager.get_summons(luna.id)
    assert len(swords) == 9


@pytest.mark.asyncio
async def test_luna_sword_hits_feed_passive_stacks():
    node = _boss_node()
    party = _basic_party()
    luna = Luna()
    luna.id = "luna_stack"
    luna.rank = "boss"

    await setup_battle(node, party, foe=luna)

    swords = SummonManager.get_summons(luna.id)
    assert swords, "Boss Luna should summon swords"
    sword = swords[0]

    assert sword.max_hp == luna.max_hp
    assert sword.atk == luna.atk

    target = Stats()
    target.id = "target"
    target.hp = target.max_hp

    before = LunaLunarReservoir.get_charge(luna)
    await BUS.emit_async("hit_landed", sword, target, 100, "attack", "test")
    after = LunaLunarReservoir.get_charge(luna)

    assert after - before == 4
    assert LunaLunarReservoir.get_charge(sword) == after


@pytest.mark.asyncio
async def test_glitched_luna_sword_hits_double_charge():
    node = _boss_node()
    party = _basic_party()
    luna = Luna()
    luna.id = "luna_glitched_stack"
    luna.rank = "glitched boss"

    await setup_battle(node, party, foe=luna)

    swords = SummonManager.get_summons(luna.id)
    assert swords, "Glitched boss Luna should summon swords"
    sword = swords[0]

    target = Stats()
    target.id = "dummy"
    target.hp = target.max_hp

    before = LunaLunarReservoir.get_charge(luna)
    await BUS.emit_async("hit_landed", sword, target, 100, "attack", "test")
    after = LunaLunarReservoir.get_charge(luna)

    assert after - before == 8


@pytest.mark.asyncio
async def test_luna_non_glitched_ranks_detach_helper():
    node = _normal_node()
    party = _basic_party()
    luna = Luna()
    luna.id = "luna_normal"
    luna.rank = "champion"

    await setup_battle(node, party, foe=luna)

    helper = getattr(luna, "_luna_sword_helper", None)
    assert helper is None
    assert not SummonManager.get_summons(luna.id)


@pytest.mark.asyncio
async def test_luna_glitched_non_boss_gets_lightstream_swords(monkeypatch):
    sequence = iter(["Fire", "Ice"])

    def _choice(options):
        try:
            candidate = next(sequence)
        except StopIteration:
            candidate = options[0]
        if candidate not in options:
            return options[0]
        return candidate

    monkeypatch.setattr("plugins.characters.luna.random.choice", _choice)

    node = _normal_node()
    party = _basic_party()
    luna = Luna()
    luna.id = "luna_glitched_nonboss"
    luna.rank = "glitched champion"

    await setup_battle(node, party, foe=luna)

    swords = SummonManager.get_summons(luna.id)
    assert len(swords) == 2
    assert {getattr(s, "luna_sword_label", None) for s in swords} == {"Lightstream"}
    assert all(getattr(s, "summon_type", "") == "luna_sword_lightstream" for s in swords)
    damage_ids = {getattr(getattr(s, "damage_type", None), "id", None) for s in swords}
    assert damage_ids == {"Fire", "Ice"}
