import pytest

from autofighter.party import Party
from autofighter.stats import BUS
from plugins.cards.flux_paradox_engine import FluxParadoxEngine
from plugins.characters.ally import Ally
from plugins.characters.foe_base import FoeBase
from plugins.dots.blazing_torment import BlazingTorment
from plugins.dots.cold_wound import ColdWound


@pytest.mark.asyncio
async def test_flux_paradox_engine_fire_stance_applies_blazing_torment_once():

    ally = Ally()
    ally.id = "ally"
    foe = FoeBase()
    foe.id = "foe"
    party = Party(members=[ally])

    card = FluxParadoxEngine()
    await card.apply(party)

    events: list[tuple[str, int, dict[str, object]]] = []

    async def _on_card_effect(card_id, _actor, effect_name, amount, extra):
        if card_id == card.id:
            events.append((effect_name, amount, extra))

    BUS.subscribe("card_effect", _on_card_effect)
    try:
        await BUS.emit_async("battle_start", ally)
        await BUS.emit_async("battle_start", foe)
        await BUS.emit_async("turn_start", ally)
        await BUS.emit_async("hit_landed", ally, foe, 100, "attack")

        mgr = getattr(foe, "effect_manager", None)
        assert mgr is not None
        blazing = [dot for dot in mgr.dots if dot.id == BlazingTorment.id]
        assert len(blazing) == 1

        await BUS.emit_async("hit_landed", ally, foe, 80, "attack")
        assert len([dot for dot in mgr.dots if dot.id == BlazingTorment.id]) == 1

        fire_events = [name for name, *_ in events if name == "fire_stance_dot"]
        assert len(fire_events) == 1
    finally:
        BUS.unsubscribe("card_effect", _on_card_effect)
        await BUS.emit_async("battle_end", ally)
        await BUS.emit_async("battle_end", foe)


@pytest.mark.asyncio
async def test_flux_paradox_engine_ice_stance_applies_cold_wound_and_mitigation():

    ally = Ally()
    ally.id = "ally"
    base_mitigation = ally.mitigation
    foe = FoeBase()
    foe.id = "foe"
    party = Party(members=[ally])

    card = FluxParadoxEngine()
    await card.apply(party)

    events: list[tuple[str, int, dict[str, object]]] = []

    async def _on_card_effect(card_id, _actor, effect_name, amount, extra):
        if card_id == card.id:
            events.append((effect_name, amount, extra))

    BUS.subscribe("card_effect", _on_card_effect)
    try:
        await BUS.emit_async("battle_start", ally)
        await BUS.emit_async("battle_start", foe)
        await BUS.emit_async("turn_start", ally)
        await BUS.emit_async("turn_start", foe)
        await BUS.emit_async("hit_landed", ally, foe, 120, "attack")

        mgr = getattr(foe, "effect_manager", None)
        assert mgr is not None
        cold = [dot for dot in mgr.dots if dot.id == ColdWound.id]
        assert len(cold) == 1

        ally_mgr = getattr(ally, "effect_manager", None)
        assert ally_mgr is not None
        assert any(mod.id == f"{card.id}_mitigation" for mod in ally_mgr.mods)
        assert ally.mitigation >= base_mitigation

        ice_events = [name for name, *_ in events if name == "ice_stance_dot"]
        assert len(ice_events) == 1
    finally:
        BUS.unsubscribe("card_effect", _on_card_effect)
        await BUS.emit_async("battle_end", ally)
        await BUS.emit_async("battle_end", foe)


@pytest.mark.asyncio
async def test_flux_paradox_engine_resets_between_stances():

    ally = Ally()
    ally.id = "ally"
    foe = FoeBase()
    foe.id = "foe"
    party = Party(members=[ally])

    card = FluxParadoxEngine()
    await card.apply(party)

    events: list[str] = []

    async def _on_card_effect(card_id, _actor, effect_name, *_extra):
        if card_id == card.id:
            events.append(effect_name)

    BUS.subscribe("card_effect", _on_card_effect)
    try:
        await BUS.emit_async("battle_start", ally)
        await BUS.emit_async("battle_start", foe)

        await BUS.emit_async("turn_start", ally)
        await BUS.emit_async("hit_landed", ally, foe, 90, "attack")

        await BUS.emit_async("turn_start", foe)
        await BUS.emit_async("hit_landed", ally, foe, 95, "attack")

        await BUS.emit_async("turn_start", ally)
        await BUS.emit_async("hit_landed", ally, foe, 110, "attack")

        fire_events = [name for name in events if name == "fire_stance_dot"]
        ice_events = [name for name in events if name == "ice_stance_dot"]

        assert len(fire_events) == 2
        assert len(ice_events) == 1
    finally:
        BUS.unsubscribe("card_effect", _on_card_effect)
        await BUS.emit_async("battle_end", ally)
        await BUS.emit_async("battle_end", foe)
