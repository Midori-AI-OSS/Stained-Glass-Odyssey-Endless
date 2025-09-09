"""Tests for the diminishing returns buff scaling system."""

from autofighter.effects import calculate_diminishing_returns
from autofighter.effects import create_stat_buff
from autofighter.effects import get_current_stat_value
from autofighter.stats import Stats


class TestDiminishingReturnsCalculation:
    """Test the core diminishing returns calculation logic."""

    def test_hp_scaling(self):
        """Test HP diminishing returns: 4x per 500 HP."""
        # Below threshold: full effectiveness
        assert calculate_diminishing_returns("max_hp", 400) == 1.0

        # At 500 HP: 4x less effective (0.25x effectiveness)
        expected_500 = 1.0 / (4.0**1)
        assert abs(calculate_diminishing_returns("max_hp", 500) - expected_500) < 1e-6

        # At 1000 HP: 16x less effective (0.0625x effectiveness)
        expected_1000 = 1.0 / (4.0**2)
        assert abs(calculate_diminishing_returns("max_hp", 1000) - expected_1000) < 1e-6

        # At 1500 HP: 64x less effective
        expected_1500 = 1.0 / (4.0**3)
        assert abs(calculate_diminishing_returns("max_hp", 1500) - expected_1500) < 1e-6

    def test_atk_def_scaling(self):
        """Test ATK/DEF diminishing returns: 100x per 100 points."""
        # Below threshold: full effectiveness
        assert calculate_diminishing_returns("atk", 50) == 1.0

        # At 100 ATK: 100x less effective (0.01x effectiveness)
        expected_100 = 1.0 / (100.0**1)
        assert abs(calculate_diminishing_returns("atk", 100) - expected_100) < 1e-6

        # At 200 ATK: 10000x less effective
        expected_200 = 1.0 / (100.0**2)
        assert abs(calculate_diminishing_returns("atk", 200) - expected_200) < 1e-6

        # At 300 ATK: 1000000x less effective
        expected_300 = 1.0 / (100.0**3)
        assert abs(calculate_diminishing_returns("atk", 300) - expected_300) < 1e-6

        # Same rules apply to defense
        assert abs(calculate_diminishing_returns("defense", 100) - expected_100) < 1e-6

    def test_percentage_stat_scaling(self):
        """Test crit rate: 100x per 1% over 75%. Mitigation, vitality: 100x per 1% over 2%."""
        # Crit rate at base (75%) or below: full effectiveness
        assert calculate_diminishing_returns("crit_rate", 0.75) == 1.0
        assert calculate_diminishing_returns("crit_rate", 0.50) == 1.0  # Below base

        # At 76% (1% over base): 1/100 effectiveness
        expected_76pct = 1.0 / (100.0**1)
        assert (
            abs(calculate_diminishing_returns("crit_rate", 0.76) - expected_76pct)
            < 1e-6
        )

        # At 77% (2% over base): 1/10000 effectiveness
        expected_77pct = 1.0 / (100.0**2)
        assert (
            abs(calculate_diminishing_returns("crit_rate", 0.77) - expected_77pct)
            < 1e-6
        )

        # Mitigation and vitality still use 2% base
        expected_3pct = 1.0 / (100.0**1)
        assert calculate_diminishing_returns("mitigation", 0.03) == expected_3pct
        assert calculate_diminishing_returns("vitality", 0.03) == expected_3pct

    def test_crit_damage_scaling(self):
        """Test crit damage: 1000x per 500%."""
        # At base (200%): full effectiveness
        assert calculate_diminishing_returns("crit_damage", 2.0) == 1.0
        assert calculate_diminishing_returns("crit_damage", 1.0) == 1.0  # Below base

        # At 700% (500% over base): 1/1000 effectiveness
        expected_700 = 1.0 / (1000.0**1)
        assert (
            abs(calculate_diminishing_returns("crit_damage", 7.0) - expected_700) < 1e-6
        )

        # At 1200% (1000% over base): 1/1000000 effectiveness
        expected_1200 = 1.0 / (1000.0**2)
        assert (
            abs(calculate_diminishing_returns("crit_damage", 12.0) - expected_1200)
            < 1e-6
        )

    def test_unconfigured_stats(self):
        """Test that unconfigured stats have no diminishing returns."""
        assert calculate_diminishing_returns("unknown_stat", 9999) == 1.0
        assert calculate_diminishing_returns("exp", 5000) == 1.0

    def test_numerical_limits(self):
        """Test that extreme values don't cause numerical issues."""
        # Very high values should still return a valid scaling factor
        result = calculate_diminishing_returns("max_hp", 50000)  # 100 steps of 500
        assert 0 < result <= 1.0
        assert result >= 1e-6  # Minimum effectiveness

        # Negative values should not cause issues
        assert calculate_diminishing_returns("atk", -100) == 1.0


class TestStatValueRetrieval:
    """Test the get_current_stat_value helper function."""

    def test_basic_stat_retrieval(self):
        """Test retrieving current stat values from Stats object."""
        stats = Stats(hp=1200)
        stats.set_base_stat("atk", 300)
        stats.set_base_stat("defense", 250)

        assert get_current_stat_value(stats, "max_hp") == stats.max_hp
        assert get_current_stat_value(stats, "atk") == stats.atk
        assert get_current_stat_value(stats, "defense") == stats.defense

    def test_percentage_stat_retrieval(self):
        """Test retrieving percentage-based stats."""
        stats = Stats()

        assert get_current_stat_value(stats, "crit_rate") == stats.crit_rate
        assert get_current_stat_value(stats, "crit_damage") == stats.crit_damage
        assert get_current_stat_value(stats, "mitigation") == stats.mitigation
        assert get_current_stat_value(stats, "vitality") == stats.vitality

    def test_fallback_behavior(self):
        """Test fallback for unmapped stat names."""
        stats = Stats()

        # Should fallback to direct attribute access
        assert get_current_stat_value(stats, "level") == stats.level
        assert get_current_stat_value(stats, "exp") == stats.exp

        # Should return 0 for non-existent attributes
        assert get_current_stat_value(stats, "nonexistent") == 0


class TestBuffScalingIntegration:
    """Test that buffs are properly scaled when applied."""

    def test_hp_buff_scaling(self):
        """Test that HP buffs are scaled based on current HP."""
        # Character with low HP should get full buff effectiveness
        low_hp_stats = Stats()
        low_hp_stats.set_base_stat("max_hp", 400)
        create_stat_buff(low_hp_stats, max_hp=100, turns=1, name="hp_buff_low")

        # Should get the full 100 HP buff
        assert low_hp_stats.max_hp == 400 + 100

        # Character with high HP should get reduced buff effectiveness
        high_hp_stats = Stats()
        high_hp_stats.set_base_stat("max_hp", 1000)  # 2 steps of 500 each
        expected_scaling = 1.0 / (4.0**2)  # 2 steps = 16x reduction

        create_stat_buff(high_hp_stats, max_hp=100, turns=1, name="hp_buff_high")
        expected_buff = 100 * expected_scaling  # 6.25

        # Should get scaled buff (6.25% of original)
        assert abs(high_hp_stats.max_hp - (1000 + expected_buff)) < 1

    def test_atk_buff_scaling(self):
        """Test that ATK buffs are scaled based on current ATK."""
        # Character with low ATK gets full effectiveness
        low_atk_stats = Stats()
        low_atk_stats.set_base_stat("atk", 50)
        create_stat_buff(low_atk_stats, atk=50, turns=1, name="atk_buff_low")
        assert low_atk_stats.atk == 50 + 50

        # Character with high ATK gets reduced effectiveness
        high_atk_stats = Stats()
        high_atk_stats.set_base_stat("atk", 200)  # Over 100 threshold
        expected_scaling = 1.0 / (100.0**1)  # 1 step over threshold

        create_stat_buff(high_atk_stats, atk=50, turns=1, name="atk_buff_high")
        expected_buff = 50 * expected_scaling

        assert abs(high_atk_stats.atk - (200 + expected_buff)) < 1

    def test_multiplicative_buff_scaling(self):
        """Test that multiplicative buffs are also scaled."""
        stats = Stats()
        stats.set_base_stat("atk", 200)  # High ATK for scaling

        # 2x multiplier should be scaled down
        create_stat_buff(stats, atk_mult=2.0, turns=1, name="mult_buff")

        # Base additive change would be: 200 * (2.0 - 1.0) = 200
        # With scaling (1/10000): 200 * 0.0001 = 0.02
        # Final ATK should be: 200 + 0.02 = 200.02
        expected_final = 200 + (200 * 0.0001)
        assert abs(stats.atk - expected_final) < 0.1

    def test_percentage_stat_buff_scaling(self):
        """Test scaling for percentage-based stats."""
        # High crit rate character (77% = 2% over 75% base)
        stats = Stats()
        stats.set_base_stat("crit_rate", 0.77)
        expected_scaling = 1.0 / (100.0**2)  # 2 steps over 75% base

        create_stat_buff(stats, crit_rate=0.01, turns=1, name="crit_buff")
        expected_buff = 0.01 * expected_scaling

        assert abs(stats.crit_rate - (0.77 + expected_buff)) < 1e-6

    def test_multiple_buffs_accumulate_scaling(self):
        """Test that multiple buffs each get their own scaling."""
        stats = Stats()
        stats.set_base_stat("max_hp", 1000)  # High HP for scaling

        # Both buffs get scaled based on starting HP of 1000
        expected_scaling = 1.0 / (4.0**2)  # 2 steps = 16x reduction
        create_stat_buff(stats, max_hp=100, turns=1, name="buff1")
        create_stat_buff(stats, max_hp=100, turns=1, name="buff2")

        # Each buff contributes 100 * 0.0625 = 6.25
        # Total should be 1000 + 6.25 + 6.25 = 1012.5
        expected_total = 1000 + (100 * expected_scaling * 2)

        assert abs(stats.max_hp - expected_total) < 1


class TestEdgeCases:
    """Test edge cases and potential issues."""

    def test_negative_buffs_are_scaled(self):
        """Test that debuffs (negative buffs) are also scaled."""
        stats = Stats()
        stats.set_base_stat("atk", 200)  # High ATK
        expected_scaling = 1.0 / (100.0**1)

        # Negative buff should also be scaled
        create_stat_buff(stats, atk=-50, turns=1, name="debuff")
        expected_change = -50 * expected_scaling  # -0.5

        assert abs(stats.atk - (200 + expected_change)) < 1

    def test_zero_value_buffs(self):
        """Test that zero-value buffs don't cause issues."""
        stats = Stats()
        stats.set_base_stat("atk", 200)

        # Zero buff should work fine
        create_stat_buff(stats, atk=0, turns=1, name="zero_buff")
        assert stats.atk == 200  # No change

    def test_very_small_buffs(self):
        """Test that very small buffs still work correctly."""
        stats = Stats()
        stats.set_base_stat("max_hp", 2000)  # Very high HP for extreme scaling

        # Even with extreme scaling, should still apply some effect
        create_stat_buff(stats, max_hp=1000, turns=1, name="big_buff")

        # Should be > base HP due to some effect, even if tiny
        assert stats.max_hp > 2000
