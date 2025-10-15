import pytest

from autofighter.cards import award_card
from autofighter.mapgen import MapNode
from autofighter.party import Party
from autofighter.relics import award_relic
from autofighter.rooms.battle.setup import setup_battle
from autofighter.stats import Stats


def _make_node() -> MapNode:
    return MapNode(room_id=0, room_type="battle-normal", floor=1, index=1, loop=1, pressure=0)


def _make_member() -> Stats:
    member = Stats()
    member.id = "hero"
    member.hp = member.max_hp
    return member


def _make_foe() -> Stats:
    foe = Stats()
    foe.id = "foe"
    foe.hp = foe.max_hp
    return foe


@pytest.mark.asyncio
async def test_card_effect_persists_across_battles():
    node = _make_node()
    base_member = _make_member()
    base_member.atk = 100
    party = Party(members=[base_member], cards=["micro_blade"], relics=[], rdr=1.0)

    first = await setup_battle(node, party, foe=_make_foe())
    first_member = first.combat_party.members[0]
    assert first_member.atk > 100

    party.members = first.combat_party.members

    second = await setup_battle(node, party, foe=_make_foe())
    second_member = second.combat_party.members[0]
    assert second_member.atk == pytest.approx(first_member.atk)
    assert any(mod.startswith("micro_blade") for mod in second_member.mods)

    award_card(party, "iron_guard")
    party.members = second.combat_party.members

    third = await setup_battle(node, party, foe=_make_foe())
    third_member = third.combat_party.members[0]
    assert third_member.defense > second_member.defense


@pytest.mark.asyncio
async def test_relic_stack_refreshes_when_count_changes():
    node = _make_node()
    base_member = _make_member()
    base_member.atk = 120
    party = Party(members=[base_member], cards=[], relics=["bent_dagger"], rdr=1.0)

    first = await setup_battle(node, party, foe=_make_foe())
    first_member = first.combat_party.members[0]
    assert first_member.atk > 120

    party.members = first.combat_party.members

    second = await setup_battle(node, party, foe=_make_foe())
    second_member = second.combat_party.members[0]
    assert second_member.atk == pytest.approx(first_member.atk)

    award_relic(party, "bent_dagger")
    party.members = second.combat_party.members

    third = await setup_battle(node, party, foe=_make_foe())
    third_member = third.combat_party.members[0]
    assert third_member.atk > second_member.atk
