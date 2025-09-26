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
async def test_guiding_compass_first_battle_xp_only_once() -> None:
    event_bus_module.bus._subs.clear()

    member1 = PlayerBase()
    member1.id = "m1"
    member2 = PlayerBase()
    member2.id = "m2"
    party = Party([member1, member2])
    base_exp = member1.exp
    pre_battle_start = len(event_bus_module.bus._subs.get("battle_start", []))
    pre_battle_end = len(event_bus_module.bus._subs.get("battle_end", []))

    card = GuidingCompass()
    await card.apply(party)

    assert len(event_bus_module.bus._subs.get("battle_start", [])) == pre_battle_start + 1
    assert len(event_bus_module.bus._subs.get("battle_end", [])) == pre_battle_end + 1

    events: list[tuple[str, str, int]] = []

    async def _on_card_effect(card_id, member, effect, amount, extra):
        if effect == "first_battle_xp":
            events.append((card_id, member.id, amount))

    BUS.subscribe("card_effect", _on_card_effect)

    await BUS.emit_async("battle_start", member1)
    await asyncio.sleep(0.05)

    assert member1.exp == base_exp + 10
    assert member2.exp == base_exp + 10
    assert len(events) == 2

    await BUS.emit_async("battle_start", member1)
    await asyncio.sleep(0.05)

    assert member1.exp == base_exp + 10
    assert member2.exp == base_exp + 10
    assert len(events) == 2

    await BUS.emit_async("battle_end")
    await asyncio.sleep(0.05)

    assert len(event_bus_module.bus._subs.get("battle_start", [])) == pre_battle_start
    assert len(event_bus_module.bus._subs.get("battle_end", [])) == pre_battle_end

    second_card = GuidingCompass()
    await second_card.apply(party)

    assert len(event_bus_module.bus._subs.get("battle_start", [])) == pre_battle_start + 1
    assert len(event_bus_module.bus._subs.get("battle_end", [])) == pre_battle_end + 1

    await BUS.emit_async("battle_end")
    await asyncio.sleep(0.05)

    assert len(event_bus_module.bus._subs.get("battle_start", [])) == pre_battle_start
    assert len(event_bus_module.bus._subs.get("battle_end", [])) == pre_battle_end

    BUS.unsubscribe("card_effect", _on_card_effect)

