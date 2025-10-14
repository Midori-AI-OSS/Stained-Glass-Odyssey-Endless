# ruff: noqa: E402

import asyncio
import sys
import types

import pytest

torch_checker = types.ModuleType("torch_checker")
torch_checker.is_torch_available = lambda: False
llms_module = types.ModuleType("llms")
llms_module.torch_checker = torch_checker
sys.modules["llms"] = llms_module
sys.modules["llms.torch_checker"] = torch_checker

from autofighter.party import Party
from autofighter.stats import BUS
from plugins.cards.guiding_compass import GuidingCompass
import plugins.event_bus as event_bus_module
from plugins.characters._base import PlayerBase


@pytest.mark.asyncio
async def test_guiding_compass_levels_party_only_once() -> None:
    event_bus_module.bus._subs.clear()

    member1 = PlayerBase()
    member1.id = "m1"
    member2 = PlayerBase()
    member2.id = "m2"
    party = Party([member1, member2])
    base_levels = [member.level for member in party.members]

    events: list[tuple[str, str, str, int, int]] = []

    async def _on_card_effect(card_id, member, effect, amount, extra):
        if effect == "instant_level_up":
            events.append((card_id, member.id, effect, extra.get("previous_level", 0), extra.get("new_level", 0)))

    BUS.subscribe("card_effect", _on_card_effect)

    card = GuidingCompass()
    await card.apply(party)
    await asyncio.sleep(0.05)

    assert [member.level for member in party.members] == [level + 1 for level in base_levels]
    assert getattr(party, "guiding_compass_level_up_awarded", False) is True
    assert len(events) == 2
    for idx, ((_, member_id, _, previous_level, new_level), member) in enumerate(zip(events, party.members)):
        assert member_id == member.id
        assert previous_level == base_levels[idx]
        assert new_level == member.level

    second_card = GuidingCompass()
    await second_card.apply(party)
    await asyncio.sleep(0.05)

    assert [member.level for member in party.members] == [level + 1 for level in base_levels]
    assert len(events) == 2

    new_member1 = PlayerBase()
    new_member1.id = "n1"
    new_member2 = PlayerBase()
    new_member2.id = "n2"
    new_party = Party([new_member1, new_member2])
    new_base_levels = [member.level for member in new_party.members]

    third_card = GuidingCompass()
    await third_card.apply(new_party)
    await asyncio.sleep(0.05)

    assert [member.level for member in new_party.members] == [level + 1 for level in new_base_levels]
    assert getattr(new_party, "guiding_compass_level_up_awarded", False) is True
    assert len(events) == 4

    BUS.unsubscribe("card_effect", _on_card_effect)

