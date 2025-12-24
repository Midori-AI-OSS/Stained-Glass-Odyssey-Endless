"""Unit tests for Progression system."""

import sys
from pathlib import Path

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.progression import ProgressionManager


class TestProgressionManager:
    """Tests for ProgressionManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.manager = ProgressionManager()
        
        # Sample character data
        self.character = {
            "id": "char1",
            "name": "Test Character",
            "base_stats": {
                "max_hp": 1000,
                "atk": 100,
                "defense": 80,
                "crit_rate": 0.05,
                "crit_damage": 2.0,
                "vitality": 1.0
            },
            "runtime": {
                "level": 1,
                "exp": 0,
                "hp": 1000,
                "max_hp": 1000
            }
        }
    
    def test_calculate_exp_required(self):
        """Test experience requirement calculation."""
        manager = ProgressionManager()
        
        # Level 1 to 2
        exp_lvl1 = manager.calculate_exp_required(1)
        assert exp_lvl1 == 100  # BASE_EXP_REQUIREMENT
        
        # Level 2 to 3
        exp_lvl2 = manager.calculate_exp_required(2)
        assert exp_lvl2 > exp_lvl1  # Should increase
        
        # Level 10 to 11
        exp_lvl10 = manager.calculate_exp_required(10)
        assert exp_lvl10 > exp_lvl2  # Should be much higher
    
    def test_calculate_total_exp_for_level(self):
        """Test total exp calculation to reach a level."""
        manager = ProgressionManager()
        
        # To reach level 1 (starting level)
        total_lvl1 = manager.calculate_total_exp_for_level(1)
        assert total_lvl1 == 0
        
        # To reach level 2
        total_lvl2 = manager.calculate_total_exp_for_level(2)
        assert total_lvl2 == 100
        
        # To reach level 3
        total_lvl3 = manager.calculate_total_exp_for_level(3)
        assert total_lvl3 > total_lvl2
    
    def test_check_level_up_insufficient_exp(self):
        """Test level-up check with insufficient experience."""
        manager = ProgressionManager()
        
        should_level, new_level, remaining = manager.check_level_up(1, 50)
        
        assert not should_level
        assert new_level == 1
        assert remaining == 50
    
    def test_check_level_up_sufficient_exp(self):
        """Test level-up check with sufficient experience."""
        manager = ProgressionManager()
        
        should_level, new_level, remaining = manager.check_level_up(1, 150)
        
        assert should_level
        assert new_level == 2
        assert remaining == 50  # 150 - 100 required
    
    def test_check_level_up_exact_exp(self):
        """Test level-up check with exact experience."""
        manager = ProgressionManager()
        
        should_level, new_level, remaining = manager.check_level_up(1, 100)
        
        assert should_level
        assert new_level == 2
        assert remaining == 0
    
    def test_apply_level_up(self):
        """Test stat growth on level-up."""
        manager = ProgressionManager()
        
        initial_hp = self.character["base_stats"]["max_hp"]
        initial_atk = self.character["base_stats"]["atk"]
        
        manager.apply_level_up(self.character, 2)
        
        # Stats should increase
        assert self.character["runtime"]["level"] == 2
        assert self.character["base_stats"]["max_hp"] > initial_hp
        assert self.character["base_stats"]["atk"] > initial_atk
        
        # HP should be healed to full
        assert self.character["runtime"]["hp"] == self.character["runtime"]["max_hp"]
    
    def test_apply_multiple_level_ups(self):
        """Test stat growth over multiple levels."""
        manager = ProgressionManager()
        
        initial_hp = self.character["base_stats"]["max_hp"]
        
        manager.apply_level_up(self.character, 5)  # Jump from 1 to 5
        
        # Stats should increase by 4 levels worth
        expected_hp_growth = ProgressionManager.STAT_GROWTH_PER_LEVEL["max_hp"] * 4
        assert self.character["base_stats"]["max_hp"] == initial_hp + expected_hp_growth
    
    def test_process_character_progression_no_level_up(self):
        """Test progression without leveling up."""
        manager = ProgressionManager()
        
        level_ups = manager.process_character_progression(self.character, 50)
        
        assert len(level_ups) == 0
        assert self.character["runtime"]["exp"] == 50
        assert self.character["runtime"]["level"] == 1
    
    def test_process_character_progression_single_level_up(self):
        """Test progression with single level-up."""
        manager = ProgressionManager()
        
        level_ups = manager.process_character_progression(self.character, 150)
        
        assert len(level_ups) == 1
        assert level_ups[0]["old_level"] == 1
        assert level_ups[0]["new_level"] == 2
        assert self.character["runtime"]["level"] == 2
        assert self.character["runtime"]["exp"] == 50  # Remaining after level-up
    
    def test_process_character_progression_multiple_level_ups(self):
        """Test progression with multiple level-ups at once."""
        manager = ProgressionManager()
        
        # Give enough exp for multiple levels
        large_exp = 500
        level_ups = manager.process_character_progression(self.character, large_exp)
        
        assert len(level_ups) > 1
        assert self.character["runtime"]["level"] > 2
    
    def test_distribute_exp_solo(self):
        """Test solo exp distribution."""
        manager = ProgressionManager()
        
        base_exp = 100.0
        char_mult = 1.5
        combat_mult = 2.0
        
        self.character["runtime"]["exp_multiplier"] = char_mult
        
        final_exp = manager.distribute_exp_solo(self.character, base_exp, combat_mult)
        
        # Should be base * char_mult * combat_mult
        assert final_exp == base_exp * char_mult * combat_mult
    
    def test_distribute_exp_shared(self):
        """Test shared exp distribution."""
        manager = ProgressionManager()
        
        char1 = {
            "id": "char1",
            "runtime": {"exp_multiplier": 1.0}
        }
        char2 = {
            "id": "char2",
            "runtime": {"exp_multiplier": 1.5}
        }
        
        base_exp = 100.0
        viewing_chars = [char1, char2]
        
        exp_dist = manager.distribute_exp_shared(viewing_chars, base_exp)
        
        assert "char1" in exp_dist
        assert "char2" in exp_dist
        assert exp_dist["char1"] > 0
        assert exp_dist["char2"] > 0
    
    def test_distribute_exp_shared_with_multipliers(self):
        """Test shared exp with combat multipliers."""
        manager = ProgressionManager()
        
        char1 = {
            "id": "char1",
            "runtime": {"exp_multiplier": 1.0}
        }
        
        base_exp = 100.0
        multipliers = {"char1": 2.0}  # Combat boost
        
        exp_dist = manager.distribute_exp_shared([char1], base_exp, multipliers)
        
        assert exp_dist["char1"] > base_exp * 0.45  # Should benefit from multiplier
    
    def test_generate_rewards_level_up(self):
        """Test reward generation on level-up."""
        manager = ProgressionManager()
        
        rewards = manager.generate_rewards(5, "level_up")
        
        assert "gold" in rewards
        assert rewards["gold"] > 0
        assert "items" in rewards
        assert "cards" in rewards
        assert "relics" in rewards
    
    def test_generate_rewards_milestone_level(self):
        """Test special rewards at milestone levels."""
        manager = ProgressionManager()
        
        # Level 5 (milestone)
        rewards_5 = manager.generate_rewards(5, "level_up")
        assert len(rewards_5["items"]) > 0
        
        # Level 10 (major milestone)
        rewards_10 = manager.generate_rewards(10, "level_up")
        assert len(rewards_10["cards"]) > 0
        
        # Level 20 (major milestone)
        rewards_20 = manager.generate_rewards(20, "level_up")
        assert len(rewards_20["relics"]) > 0
    
    def test_track_achievement(self):
        """Test achievement tracking."""
        manager = ProgressionManager()
        
        # First completion
        assert manager.track_achievement("first_win")
        assert manager.has_achievement("first_win")
        
        # Second attempt (already completed)
        assert not manager.track_achievement("first_win")
    
    def test_has_achievement(self):
        """Test achievement checking."""
        manager = ProgressionManager()
        
        assert not manager.has_achievement("test_achievement")
        
        manager.track_achievement("test_achievement")
        assert manager.has_achievement("test_achievement")
    
    def test_milestone_tracking(self):
        """Test milestone counter management."""
        manager = ProgressionManager()
        
        assert manager.get_milestone("battles_won") == 0
        
        manager.update_milestone("battles_won", 10)
        assert manager.get_milestone("battles_won") == 10
        
        manager.update_milestone("battles_won", 20)
        assert manager.get_milestone("battles_won") == 20
    
    def test_exp_growth_rate(self):
        """Test that exp requirements grow exponentially."""
        manager = ProgressionManager()
        
        exp_requirements = [manager.calculate_exp_required(lvl) for lvl in range(1, 11)]
        
        # Each requirement should be larger than the previous
        for i in range(1, len(exp_requirements)):
            assert exp_requirements[i] > exp_requirements[i-1]
        
        # Growth should be exponential (later levels much harder)
        ratio_early = exp_requirements[1] / exp_requirements[0]
        ratio_late = exp_requirements[9] / exp_requirements[8]
        assert ratio_late >= ratio_early  # Growth rate increases or stays consistent
    
    def test_stat_growth_consistency(self):
        """Test that stat growth is applied consistently."""
        manager = ProgressionManager()
        
        char1 = {
            "id": "char1",
            "base_stats": {"max_hp": 1000, "atk": 100},
            "runtime": {"level": 1, "exp": 0, "hp": 1000, "max_hp": 1000}
        }
        
        char2 = {
            "id": "char2",
            "base_stats": {"max_hp": 1000, "atk": 100},
            "runtime": {"level": 1, "exp": 0, "hp": 1000, "max_hp": 1000}
        }
        
        # Level both characters to 5
        manager.apply_level_up(char1, 5)
        manager.apply_level_up(char2, 5)
        
        # Both should have identical stats
        assert char1["base_stats"]["max_hp"] == char2["base_stats"]["max_hp"]
        assert char1["base_stats"]["atk"] == char2["base_stats"]["atk"]
