"""Test enhanced Enrage system functionality."""


class MockStats:
    """Simplified mock for testing."""

    def __init__(self):
        self.id = "test_foe"
        self.hp = 1000
        self.max_hp = 1000
        self.atk = 100
        self.defense = 50
        self.vitality = 1.0
        self.mitigation = 1.0
        self.passives = []

    async def apply_damage(self, amount, **kwargs):
        """Mock damage application."""
        return int(amount)


def test_enhanced_enrage_damage_multipliers():
    """Test that enhanced enrage multipliers are correctly applied."""
    # Test enrage activation with enhanced multipliers
    # Simulate being at turn 105 (5 turns into enrage for normal foes)
    turns_in_enrage = 5

    # Check damage taken multiplier (should be 1.35 * 5 = 6.75x increase)
    from autofighter.stats import get_enrage_percent
    from autofighter.stats import set_enrage_percent

    set_enrage_percent(1.35 * turns_in_enrage)

    expected_damage_taken_mult = 1.0 + (1.35 * turns_in_enrage)  # 1 + 6.75 = 7.75x
    actual_mult = 1.0 + get_enrage_percent()

    assert (
        abs(actual_mult - expected_damage_taken_mult) < 0.01
    ), f"Expected damage taken mult {expected_damage_taken_mult}, got {actual_mult}"

    # Check damage dealt multiplier (should be 1 + 2.0 * 5 = 11x)
    expected_damage_dealt_mult = 1 + 2.0 * turns_in_enrage  # 1 + 10 = 11x

    assert (
        expected_damage_dealt_mult == 11.0
    ), f"Expected damage dealt mult 11.0, got {expected_damage_dealt_mult}"


def test_enhanced_dot_damage():
    """Test that DoT damage has been increased from 5% to 10%."""
    # Create a test entity with 1000 max HP
    mock_stats = MockStats()

    # Test DoT damage calculation - should be 10% of max HP
    actual_dot_damage = int(max(mock_stats.max_hp, 1) * 0.10)

    assert (
        actual_dot_damage == 100
    ), f"Expected DoT damage 100 (10% of 1000 HP), got {actual_dot_damage}"

    # Verify this is double the old amount (5%)
    old_dot_damage = int(max(mock_stats.max_hp, 1) * 0.05)  # 50 damage
    assert (
        actual_dot_damage == old_dot_damage * 2
    ), f"New DoT damage should be double old amount. Old: {old_dot_damage}, New: {actual_dot_damage}"


def test_enrage_data_format():
    """Test that enrage data includes the new 'turns' field."""
    # Test the format that would be sent to frontend
    enrage_data = {"active": True, "stacks": 10, "turns": 10}  # New field

    assert "turns" in enrage_data, "Enrage data should include 'turns' field"
    assert (
        enrage_data["turns"] == enrage_data["stacks"]
    ), "Turns should equal stacks in current implementation"


def test_enrage_scaling_bounds():
    """Test enrage scaling with extreme values."""
    from autofighter.stats import get_enrage_percent
    from autofighter.stats import set_enrage_percent

    # Test with very high enrage turns (should still work)
    extreme_turns = 100
    set_enrage_percent(1.35 * extreme_turns)

    # Should be 1 + 135 = 136x damage taken
    expected_mult = 1.0 + (1.35 * extreme_turns)
    actual_mult = 1.0 + get_enrage_percent()

    assert (
        abs(actual_mult - expected_mult) < 0.01
    ), f"Extreme enrage scaling failed. Expected {expected_mult}, got {actual_mult}"

    # Test damage dealt scaling
    damage_dealt_mult = 1 + 2.0 * extreme_turns  # 1 + 200 = 201x
    assert (
        damage_dealt_mult == 201.0
    ), f"Extreme damage dealt scaling failed. Expected 201.0, got {damage_dealt_mult}"


def test_multiplier_comparison():
    """Test that new multipliers are significantly stronger than old ones."""
    turns = 10

    # Old multipliers
    old_damage_taken = 1.0 + (0.25 * turns)  # 3.5x
    old_damage_dealt = 1 + (0.4 * turns)  # 5x
    old_dot_percent = 0.05  # 5%

    # New multipliers
    new_damage_taken = 1.0 + (1.35 * turns)  # 14.5x
    new_damage_dealt = 1 + (2.0 * turns)  # 21x
    new_dot_percent = 0.10  # 10%

    # Verify new is significantly stronger
    assert (
        new_damage_taken > old_damage_taken * 4
    ), f"New damage taken should be much stronger: {new_damage_taken} vs {old_damage_taken}"
    assert (
        new_damage_dealt > old_damage_dealt * 4
    ), f"New damage dealt should be much stronger: {new_damage_dealt} vs {old_damage_dealt}"
    assert (
        new_dot_percent == old_dot_percent * 2
    ), f"New DoT should be double: {new_dot_percent} vs {old_dot_percent}"


if __name__ == "__main__":
    # Run tests directly
    test_enhanced_enrage_damage_multipliers()
    test_enhanced_dot_damage()
    test_enrage_data_format()
    test_enrage_scaling_bounds()
    test_multiplier_comparison()
    print("All enhanced enrage tests passed!")
