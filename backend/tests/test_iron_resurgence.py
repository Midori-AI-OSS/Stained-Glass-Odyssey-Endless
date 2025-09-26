import asyncio

import pytest

from autofighter.party import Party
from autofighter.stats import BUS
from plugins.cards.iron_resurgence import IronResurgence
import plugins.event_bus as event_bus_module
from plugins.characters._base import PlayerBase


@pytest.mark.asyncio
async def test_iron_resurgence_revives_and_cools_down() -> None:
    event_bus_module.bus._subs.clear()
    member = PlayerBase()
    party = Party([member])
    card = IronResurgence()
    await card.apply(party)
    assert member.defense == int(50 * 3)
    assert member.max_hp == int(1000 * 3)
    await member.apply_damage(member.max_hp)
    await asyncio.sleep(0)
    assert member.hp == int(member.max_hp * 0.1)
    await member.apply_damage(member.hp)
    await asyncio.sleep(0)
    assert member.hp == 0
    for _ in range(4):
        await BUS.emit_async("turn_start")
    await member.apply_healing(member.max_hp)
    await member.apply_damage(member.max_hp)
    await asyncio.sleep(0)
    assert member.hp == int(member.max_hp * 0.1)
