"""Test the new base stats vs runtime stats system."""

from autofighter.stats import StatEffect
from autofighter.stats import Stats


def test_base_stats_initialization():
    """Test that base stats are properly initialized."""
    stats = Stats()

    # Check that base stats are set
    assert stats.get_base_stat("max_hp") == 1000
    assert stats.get_base_stat("atk") == 200
    assert stats.get_base_stat("defense") == 200

    # Check that runtime stats match base stats initially
    assert stats.max_hp == 1000
    assert stats.atk == 200
    assert stats.defense == 200


def test_stat_effects():
    """Test that effects modify runtime stats without affecting base stats."""
    stats = Stats()

    # Store initial base stats
    base_atk = stats.get_base_stat("atk")
    base_defense = stats.get_base_stat("defense")

    # Add an effect that increases attack
    attack_effect = StatEffect(
        name="weapon_boost",
        stat_modifiers={"atk": 50, "defense": -10},
        source="test_weapon",
    )
    stats.add_effect(attack_effect)

    # Runtime stats should be modified
    assert stats.atk == base_atk + 50
    assert stats.defense == base_defense - 10

    # Base stats should remain unchanged
    assert stats.get_base_stat("atk") == base_atk
    assert stats.get_base_stat("defense") == base_defense


def test_effect_removal():
    """Test that removing effects restores original runtime stats."""
    stats = Stats()

    original_atk = stats.atk
    original_defense = stats.defense

    # Add effect
    effect = StatEffect(
        name="temporary_boost",
        stat_modifiers={"atk": 100, "defense": 50},
        source="test_card",
    )
    stats.add_effect(effect)

    # Verify effect is applied
    assert stats.atk == original_atk + 100
    assert stats.defense == original_defense + 50

    # Remove effect
    stats.remove_effect_by_name("temporary_boost")

    # Runtime stats should return to original values
    assert stats.atk == original_atk
    assert stats.defense == original_defense


def test_multiple_effects():
    """Test that multiple effects stack correctly."""
    stats = Stats()

    original_atk = stats.atk

    # Add multiple effects
    effect1 = StatEffect(name="effect1", stat_modifiers={"atk": 20}, source="source1")
    effect2 = StatEffect(name="effect2", stat_modifiers={"atk": 30}, source="source2")

    stats.add_effect(effect1)
    stats.add_effect(effect2)

    # Effects should stack
    assert stats.atk == original_atk + 20 + 30


def test_effect_replacement():
    """Test that adding an effect with the same name replaces the old one."""
    stats = Stats()

    original_atk = stats.atk

    # Add first effect
    effect1 = StatEffect(
        name="weapon_damage", stat_modifiers={"atk": 20}, source="weapon"
    )
    stats.add_effect(effect1)
    assert stats.atk == original_atk + 20

    # Add effect with same name but different value
    effect2 = StatEffect(
        name="weapon_damage", stat_modifiers={"atk": 50}, source="weapon"
    )
    stats.add_effect(effect2)

    # Should replace, not stack
    assert stats.atk == original_atk + 50


def test_remove_by_source():
    """Test removing all effects from a specific source."""
    stats = Stats()

    original_atk = stats.atk
    original_defense = stats.defense

    # Add effects from different sources
    card_effect1 = StatEffect("card1", {"atk": 10}, source="card")
    card_effect2 = StatEffect("card2", {"defense": 15}, source="card")
    relic_effect = StatEffect("relic1", {"atk": 5}, source="relic")

    stats.add_effect(card_effect1)
    stats.add_effect(card_effect2)
    stats.add_effect(relic_effect)

    # Remove all card effects
    removed_count = stats.remove_effect_by_source("card")
    assert removed_count == 2

    # Only relic effect should remain
    assert stats.atk == original_atk + 5
    assert stats.defense == original_defense


def test_temporary_effects():
    """Test temporary effects with duration."""
    stats = Stats()

    original_atk = stats.atk

    # Add temporary effect
    temp_effect = StatEffect(
        name="temp_boost", stat_modifiers={"atk": 25}, duration=2, source="buff"
    )
    stats.add_effect(temp_effect)
    assert stats.atk == original_atk + 25

    # Tick once
    stats.tick_effects()
    assert stats.atk == original_atk + 25  # Still active

    # Tick again
    stats.tick_effects()
    assert stats.atk == original_atk  # Should be expired and removed


def test_base_stat_modification():
    """Test that base stats can be modified for permanent changes like leveling."""
    stats = Stats()

    original_base_atk = stats.get_base_stat("atk")
    original_runtime_atk = stats.atk

    # Modify base stat (simulating level up)
    stats.modify_base_stat("atk", 10)

    # Both base and runtime should change
    assert stats.get_base_stat("atk") == original_base_atk + 10
    assert stats.atk == original_runtime_atk + 10
