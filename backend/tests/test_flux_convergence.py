"""Tests for Flux Convergence card mechanics."""

import asyncio

import pytest

from autofighter.cards import apply_cards as cards_module_apply_cards
from autofighter.cards import award_card
from autofighter.effects import DamageOverTime, EffectManager
from autofighter.party import Party
from autofighter.stats import BUS, Stats


@pytest.mark.asyncio
async def test_flux_convergence_effect_hit_rate():
    """Test that Flux Convergence grants +255% Effect Hit Rate."""
    party = Party(members=[Stats()])
    member = party.members[0]
    base_ehr = member.effect_hit_rate

    award_card(party, "flux_convergence")
    await cards_module_apply_cards(party)

    # +255% Effect Hit Rate
    assert member.effect_hit_rate == pytest.approx(base_ehr * 3.55, rel=0.01)


@pytest.mark.asyncio
async def test_flux_convergence_debuff_tracking():
    """Test that Flux Convergence increments counter on debuff application."""
    party = Party(members=[Stats()])
    member = party.members[0]

    # Track card effect events
    flux_events = []

    def _track_flux(card_id, entity, effect_type, value, details):
        if card_id == "flux_convergence" and effect_type == "flux_increment":
            flux_events.append({"count": value, "details": details})

    BUS.subscribe("card_effect", _track_flux)

    try:
        award_card(party, "flux_convergence")
        await cards_module_apply_cards(party)

        # Create a foe
        foe = Stats(hp=1000)
        foe.set_base_stat("max_hp", 1000)
        foe.effect_manager = EffectManager(foe)

        # Simulate battle start
        await BUS.emit_async("battle_start", foe)
        await asyncio.sleep(0)

        # Apply debuffs from party member
        for i in range(4):
            # Create a DoT (which is a debuff)
            dot = DamageOverTime(
                f"test_dot_{i}",
                damage=10,
                turns=2,
                id=f"test_dot_{i}",
                source=member,
            )
            await foe.effect_manager.add_dot(dot)

            # Emit effect_applied event
            await BUS.emit_async(
                "effect_applied",
                f"test_dot_{i}",
                foe,
                {
                    "effect_type": "dot",
                    "effect_id": f"test_dot_{i}",
                },
            )
            await asyncio.sleep(0)

        # Should have tracked 4 increments
        assert len(flux_events) >= 4

    finally:
        BUS.unsubscribe("card_effect", _track_flux)


@pytest.mark.asyncio
async def test_flux_convergence_burst_at_five():
    """Test that Flux Convergence triggers AoE damage at 5 debuff stacks."""
    party = Party(members=[Stats()])
    member = party.members[0]
    member.set_base_stat("atk", 100)

    # Track burst events
    burst_events = []

    def _track_burst(card_id, entity, effect_type, value, details):
        if card_id == "flux_convergence" and effect_type == "flux_burst_trigger":
            burst_events.append({"damage": value, "details": details})

    BUS.subscribe("card_effect", _track_burst)

    try:
        award_card(party, "flux_convergence")
        await cards_module_apply_cards(party)

        # Create two foes
        foe1 = Stats(hp=1000)
        foe1.set_base_stat("max_hp", 1000)
        foe1.effect_manager = EffectManager(foe1)
        foe2 = Stats(hp=1000)
        foe2.set_base_stat("max_hp", 1000)
        foe2.effect_manager = EffectManager(foe2)

        # Simulate battle start
        await BUS.emit_async("battle_start", foe1)
        await BUS.emit_async("battle_start", foe2)
        await asyncio.sleep(0)

        # Apply 5 debuffs
        for i in range(5):
            dot = DamageOverTime(
                f"test_dot_{i}",
                damage=10,
                turns=2,
                id=f"test_dot_{i}",
                source=member,
            )
            await foe1.effect_manager.add_dot(dot)

            await BUS.emit_async(
                "effect_applied",
                f"test_dot_{i}",
                foe1,
                {
                    "effect_type": "dot",
                    "effect_id": f"test_dot_{i}",
                },
            )
            await asyncio.sleep(0)

        # Give time for async tasks to complete
        await asyncio.sleep(0.1)

        # Should have triggered burst
        assert len(burst_events) >= 1
        # 120% ATK = 120 damage
        assert burst_events[0]["damage"] == 120

        # Both foes should have taken damage
        assert foe1.hp < 1000
        assert foe2.hp < 1000

    finally:
        BUS.unsubscribe("card_effect", _track_burst)


@pytest.mark.asyncio
async def test_flux_convergence_resistance_buff():
    """Test that Flux Convergence grants +20% Effect Resistance after burst."""
    party = Party(members=[Stats()])
    member = party.members[0]
    member.set_base_stat("atk", 100)
    member.effect_manager = EffectManager(member)

    award_card(party, "flux_convergence")
    await cards_module_apply_cards(party)

    # Create a foe
    foe = Stats(hp=1000)
    foe.set_base_stat("max_hp", 1000)
    foe.effect_manager = EffectManager(foe)

    # Simulate battle start
    await BUS.emit_async("battle_start", foe)
    await asyncio.sleep(0)

    # Check initial effect resistance
    base_resistance = member.effect_resistance

    # Apply 5 debuffs to trigger burst
    for i in range(5):
        dot = DamageOverTime(
            f"test_dot_{i}",
            damage=10,
            turns=2,
            id=f"test_dot_{i}",
            source=member,
        )
        await foe.effect_manager.add_dot(dot)

        await BUS.emit_async(
            "effect_applied",
            f"test_dot_{i}",
            foe,
            {
                "effect_type": "dot",
                "effect_id": f"test_dot_{i}",
            },
        )
        await asyncio.sleep(0)

    # Give time for async tasks
    await asyncio.sleep(0.1)

    # Member should have +20% Effect Resistance
    assert member.effect_resistance > base_resistance


@pytest.mark.asyncio
async def test_flux_convergence_counter_resets_after_trigger():
    """Test that Flux Convergence counter resets after triggering."""
    party = Party(members=[Stats()])
    member = party.members[0]
    member.set_base_stat("atk", 100)

    # Track flux events
    flux_events = []

    def _track_flux(card_id, entity, effect_type, value, details):
        if card_id == "flux_convergence" and effect_type == "flux_increment":
            flux_events.append(value)

    BUS.subscribe("card_effect", _track_flux)

    try:
        award_card(party, "flux_convergence")
        await cards_module_apply_cards(party)

        # Create a foe
        foe = Stats(hp=1000)
        foe.set_base_stat("max_hp", 1000)
        foe.effect_manager = EffectManager(foe)

        # Simulate battle start
        await BUS.emit_async("battle_start", foe)
        await asyncio.sleep(0)

        # Apply 7 debuffs (should trigger at 5, then count 2 more)
        for i in range(7):
            dot = DamageOverTime(
                f"test_dot_{i}",
                damage=10,
                turns=2,
                id=f"test_dot_{i}",
                source=member,
            )
            await foe.effect_manager.add_dot(dot)

            await BUS.emit_async(
                "effect_applied",
                f"test_dot_{i}",
                foe,
                {
                    "effect_type": "dot",
                    "effect_id": f"test_dot_{i}",
                },
            )
            await asyncio.sleep(0)

        # Give time for async tasks
        await asyncio.sleep(0.1)

        # Should have: 1, 2, 3, 4, 5 (trigger), 1, 2
        assert len(flux_events) == 7
        # Check that it reset after reaching 5
        assert flux_events[-2:] == [1, 2] or flux_events == [1, 2, 3, 4, 5, 1, 2]

    finally:
        BUS.unsubscribe("card_effect", _track_flux)

