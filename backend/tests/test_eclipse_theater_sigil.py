from __future__ import annotations

import pytest

from autofighter.effects import EffectManager
from autofighter.party import Party
from autofighter.stats import BUS
from plugins.cards.eclipse_theater_sigil import EclipseTheaterSigil
from plugins.dots.celestial_atrophy import CelestialAtrophy
from plugins.characters.foe_base import FoeBase
from plugins.characters.player import Player


@pytest.mark.asyncio
async def test_eclipse_sigil_light_turn_cleanses_and_hots() -> None:
    card = EclipseTheaterSigil()
    player = Player()
    party = Party(members=[player])
    await card.apply(party)

    manager = EffectManager(player)
    player.effect_manager = manager
    await manager.add_dot(CelestialAtrophy(10, 3))

    foe = FoeBase()

    events: list[tuple[str, dict[str, object]]] = []

    def _record(card_id, _entity, event_type, _amount, meta):
        if card_id == card.id:
            events.append((event_type, meta))

    BUS.subscribe("card_effect", _record)

    try:
        await BUS.emit_async("battle_start", player)
        await BUS.emit_async("battle_start", foe)
        await BUS.emit_async("turn_start", player)
    finally:
        BUS.unsubscribe("card_effect", _record)
        await BUS.emit_async("battle_end", None)

    assert manager.dots == []
    assert any(hot.id == "light_radiant_regeneration" for hot in manager.hots)

    light_events = [meta for event, meta in events if event == "light_polarity"]
    assert light_events, "Light telemetry should be emitted"
    payload = light_events[-1]
    assert payload["polarity"] == "Light"
    assert payload["cleansed"]
    assert payload["hots_applied"]


@pytest.mark.asyncio
async def test_eclipse_sigil_dark_turn_applies_debuff_and_consumes_crit() -> None:
    card = EclipseTheaterSigil()
    member_one = Player()
    member_two = Player()
    party = Party(members=[member_one, member_two])
    await card.apply(party)

    for member in party.members:
        manager = EffectManager(member)
        member.effect_manager = manager

    foe = FoeBase()
    foe.effect_manager = EffectManager(foe)

    events: list[tuple[str, dict[str, object]]] = []

    def _record(card_id, _entity, event_type, _amount, meta):
        if card_id == card.id:
            events.append((event_type, meta))

    BUS.subscribe("card_effect", _record)

    try:
        await BUS.emit_async("battle_start", member_one)
        await BUS.emit_async("battle_start", member_two)
        await BUS.emit_async("battle_start", foe)
        await BUS.emit_async("turn_start", member_one)
        await BUS.emit_async("turn_start", foe)

        dark_events = [meta for event, meta in events if event == "dark_polarity"]
        assert dark_events, "Dark telemetry should be emitted"
        dark_payload = dark_events[-1]
        assert dark_payload["polarity"] == "Dark"

        foe_dots = [dot for dot in foe.effect_manager.dots if dot.id == "abyssal_weakness"]
        assert foe_dots, "Foes should receive Abyssal Weakness stacks"

        crit_mod_ids = {
            modifier.id
            for member in party.members
            for modifier in member.effect_manager.mods
            if modifier.id.startswith(card.id)
        }
        assert crit_mod_ids, "Allies should have temporary crit modifiers"

        await BUS.emit_async("action_used", member_one, foe, 0)

        remaining_mods = [
            modifier
            for modifier in member_one.effect_manager.mods
            if modifier.id.startswith(card.id)
        ]
        assert not remaining_mods, "Consumed crit bonus should be removed"

        consumption_events = [meta for event, meta in events if event == "dark_crit_consumed"]
        assert consumption_events, "Consumption telemetry should be emitted"
    finally:
        BUS.unsubscribe("card_effect", _record)
        await BUS.emit_async("battle_end", None)


@pytest.mark.asyncio
async def test_eclipse_sigil_resets_between_battles() -> None:
    card = EclipseTheaterSigil()
    player = Player()
    party = Party(members=[player])
    await card.apply(party)

    player.effect_manager = EffectManager(player)

    foe = FoeBase()

    await BUS.emit_async("battle_start", player)
    await BUS.emit_async("battle_start", foe)
    await BUS.emit_async("turn_start", player)
    await BUS.emit_async("turn_start", foe)
    await BUS.emit_async("battle_end", None)

    # Apply a fresh DoT and ensure the next Light turn still cleanses
    player.effect_manager = EffectManager(player)
    await player.effect_manager.add_dot(CelestialAtrophy(10, 3))

    await BUS.emit_async("battle_start", player)
    await BUS.emit_async("battle_start", foe)
    await BUS.emit_async("turn_start", player)

    assert player.effect_manager.dots == []
    await BUS.emit_async("battle_end", None)
