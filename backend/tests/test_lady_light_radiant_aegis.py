import asyncio

import pytest

from autofighter.stats import BUS
from autofighter.stats import Stats
from plugins.passives.normal.lady_light_radiant_aegis import LadyLightRadiantAegis


@pytest.mark.asyncio
async def test_radiant_aegis_shields_persist_after_tick():
    passive = LadyLightRadiantAegis()
    healer = Stats()
    ally = Stats()

    ally.shields = 0
    ally.overheal_enabled = False

    await passive.apply(healer)
    await passive.on_hot_applied(healer, ally, hot_amount=200)

    assert ally.overheal_enabled is True
    assert ally.shields == 100

    hot_res_effect = f"{passive.id}_hot_resistance"
    assert any(effect.name == hot_res_effect for effect in ally.get_active_effects())

    ally.tick_effects()

    assert not any(effect.name == hot_res_effect for effect in ally.get_active_effects())
    assert ally.shields == 100


@pytest.mark.asyncio
async def test_radiant_aegis_cleanse_heal_emits_event():
    passive = LadyLightRadiantAegis()
    target = Stats()
    ally = Stats()

    await passive.apply(target)
    expected_heal = int(ally.max_hp * 0.05)
    ally.hp = ally.max_hp - 200

    events: list[tuple[Stats, Stats, int, str, str]] = []

    def _on_heal_received(tgt, healer, amount, source_type, source_name):
        events.append((tgt, healer, amount, source_type, source_name))

    BUS.subscribe("heal_received", _on_heal_received)

    try:
        await passive.on_dot_cleanse(target, ally)
        await asyncio.sleep(0.05)
    finally:
        BUS.unsubscribe("heal_received", _on_heal_received)

    assert ally.hp == ally.max_hp - 200 + expected_heal

    assert any(
        event[0] is ally
        and event[1] is target
        and event[2] == expected_heal
        and event[3] == "cleanse"
        and event[4] == passive.id
        for event in events
    )
