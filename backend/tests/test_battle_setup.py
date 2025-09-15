import pytest

from autofighter.mapgen import MapNode
from autofighter.party import Party
from autofighter.rooms.battle.setup import setup_battle
from autofighter.stats import Stats


@pytest.mark.asyncio
async def test_setup_battle_prepares_combat_state():
    node = MapNode(room_id=0, room_type="battle-normal", floor=1, index=1, loop=1, pressure=0)

    member = Stats()
    member.id = "hero"
    member.hp = member.max_hp

    foe = Stats()
    foe.id = "foe"
    foe.hp = foe.max_hp

    party = Party(members=[member], gold=25, relics=[], cards=[], rdr=1.0)

    result = await setup_battle(node, party, foe=foe)

    assert result.registry is not None
    assert result.combat_party is not party
    assert len(result.combat_party.members) == 1
    prepared_member = result.combat_party.members[0]
    assert prepared_member is not member
    assert prepared_member.effect_manager is not None
    assert result.foes == [foe]
    assert foe.effect_manager is not None
    assert len(result.enrage_mods) == len(result.foes)
    assert result.visual_queue is not None
    assert party.rdr == result.combat_party.rdr
    assert result.battle_logger is None
