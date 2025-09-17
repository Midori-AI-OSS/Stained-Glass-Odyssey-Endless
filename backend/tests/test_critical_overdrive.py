import asyncio

import asyncio

import pytest

from autofighter.party import Party
from plugins.cards.critical_overdrive import CriticalOverdrive
from plugins.effects.critical_boost import CriticalBoost
import plugins.event_bus as event_bus_module
from plugins.players._base import PlayerBase


@pytest.mark.asyncio
async def test_critical_overdrive_boosts_and_converts() -> None:
    event_bus_module.bus._subs.clear()
    member = PlayerBase()
    party = Party([member])
    card = CriticalOverdrive()
    await card.apply(party)
    boost = CriticalBoost()
    for _ in range(200):
        await boost.apply(member)
    assert member.atk == int(100 * 3.55)
    assert member.crit_rate == pytest.approx(1.15)
    assert member.crit_damage == pytest.approx(12.3)
    await boost._on_damage_taken(member)
    await asyncio.sleep(0)
    assert member.crit_rate == pytest.approx(0.05)
    assert member.crit_damage == pytest.approx(2.0)
