"""Test for the Dark Resonance buff fix."""

from autofighter.effects import EffectManager
from autofighter.stats import Stats
from plugins import damage_effects
from plugins.damage_types.dark import Dark


def test_dark_resonance_buff_has_proper_name():
    """Test that the dark damage type creates a properly named buff."""
    dark = Dark()

    # Create attacker and target
    attacker = Stats()
    attacker.damage_type = dark
    attacker._base_atk = 100
    attacker._base_defense = 50
    attacker.effect_manager = EffectManager(attacker)

    target = Stats()
    target._base_max_hp = 1000
    target.dots = [damage_effects.SHADOW_SIPHON_ID]  # Has shadow siphon

    # Call the method that creates the buff
    damage_amount = 100  # 10% of max HP
    result = dark.on_party_dot_damage_taken(damage_amount, attacker, target)

    # Check that damage is returned unchanged
    assert result == damage_amount

    # Check that a modifier was added with the correct name
    mods = attacker.effect_manager.mods
    assert len(mods) == 1
    assert mods[0].name == "Dark Resonance"
    assert mods[0].id == "dark_resonance"
    assert mods[0].turns == 9999


def test_dark_resonance_buff_no_effect_without_shadow_siphon():
    """Test that no buff is created if target doesn't have shadow siphon."""
    dark = Dark()

    # Create attacker and target
    attacker = Stats()
    attacker.damage_type = dark
    attacker._base_atk = 100
    attacker._base_defense = 50
    attacker.effect_manager = EffectManager(attacker)

    target = Stats()
    target._base_max_hp = 1000
    target.dots = []  # No shadow siphon

    # Call the method that creates the buff
    damage_amount = 100
    result = dark.on_party_dot_damage_taken(damage_amount, attacker, target)

    # Check that damage is returned unchanged
    assert result == damage_amount

    # Check that no modifier was added
    mods = attacker.effect_manager.mods
    assert len(mods) == 0


def test_dark_resonance_buff_no_effect_with_non_dark_attacker():
    """Test that no buff is created if attacker is not dark type."""
    dark = Dark()

    # Create attacker and target
    attacker = Stats()
    # Don't set damage_type to dark
    attacker._base_atk = 100
    attacker._base_defense = 50
    attacker.effect_manager = EffectManager(attacker)

    target = Stats()
    target._base_max_hp = 1000
    target.dots = [damage_effects.SHADOW_SIPHON_ID]  # Has shadow siphon

    # Call the method that creates the buff
    damage_amount = 100
    result = dark.on_party_dot_damage_taken(damage_amount, attacker, target)

    # Check that damage is returned unchanged
    assert result == damage_amount

    # Check that no modifier was added
    mods = attacker.effect_manager.mods
    assert len(mods) == 0
