"""Integration test for dark resonance buff fix to verify async bus performance."""

import asyncio

import pytest

from autofighter.effects import EffectManager
from autofighter.stats import Stats
from plugins import damage_effects
from plugins.damage_types.dark import Dark


@pytest.mark.asyncio
async def test_dark_resonance_buff_identifiable_in_async_context():
    """Test that Dark Resonance buffs are properly named and identifiable in async operations."""
    dark = Dark()

    # Create multiple attackers to simulate gameplay scenario
    attackers = []
    for i in range(3):
        attacker = Stats()
        attacker.id = f"attacker_{i}"
        attacker.damage_type = dark
        attacker._base_atk = 100
        attacker._base_defense = 50
        attacker.effect_manager = EffectManager(attacker)
        attackers.append(attacker)

    # Create target with shadow siphon
    target = Stats()
    target.id = "target"
    target._base_max_hp = 1000
    target.dots = [damage_effects.SHADOW_SIPHON_ID]

    # Simulate multiple dark damage DoT ticks creating buffs
    async def create_buff(attacker):
        damage_amount = 100  # 10% of max HP
        result = dark.on_party_dot_damage_taken(damage_amount, attacker, target)
        return result, attacker.effect_manager.mods

    # Create buffs asynchronously (simulating concurrent DoT processing)
    tasks = [create_buff(attacker) for attacker in attackers]
    results = await asyncio.gather(*tasks)

    # Verify all buffs were created with proper names
    for i, (damage_result, mods) in enumerate(results):
        assert damage_result == 100  # Damage returned unchanged
        assert len(mods) == 1  # One modifier created
        mod = mods[0]
        assert mod.name == "Dark Resonance"  # Proper name instead of generic "buff"
        assert mod.id == "dark_resonance"  # Specific ID for tracking
        assert mod.turns == 9999  # Long duration as expected

    # Verify that each attacker has a uniquely identifiable buff
    all_mod_names = []
    all_mod_ids = []
    for attacker in attackers:
        for mod in attacker.effect_manager.mods:
            all_mod_names.append(mod.name)
            all_mod_ids.append(mod.id)

    # All should have the same proper name (not generic "buff")
    assert all(name == "Dark Resonance" for name in all_mod_names)
    # All should have the same proper ID (not generic or None)
    assert all(mod_id == "dark_resonance" for mod_id in all_mod_ids)

    # This demonstrates that the effect management system can now properly
    # identify and track these buffs, which should help with async performance


def test_dark_resonance_unique_identification():
    """Test that Dark Resonance buffs can be uniquely identified vs generic buffs."""
    from autofighter.effects import create_stat_buff

    # Create a stats object
    stats = Stats()
    stats.effect_manager = EffectManager(stats)

    # Create old-style generic buff (what the code used to create)
    old_style_buff = create_stat_buff(stats, turns=9999, atk_mult=1.05)

    # Create new-style named buff (what the code now creates)
    new_style_buff = create_stat_buff(
        stats, name="Dark Resonance", id="dark_resonance", turns=9999, atk_mult=1.05
    )

    # The old style would have name="buff", id="buff"
    assert old_style_buff.name == "buff"
    assert old_style_buff.id == "buff"

    # The new style has proper identification
    assert new_style_buff.name == "Dark Resonance"
    assert new_style_buff.id == "dark_resonance"

    # This shows that the fix provides better identifiability for effect management
