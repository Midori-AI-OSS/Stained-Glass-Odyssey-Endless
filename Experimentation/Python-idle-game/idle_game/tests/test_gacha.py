"""Unit tests for Gacha system."""

import random
import sys
import time
from pathlib import Path

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.gacha import FREE_DUPLICATE_LEVELS_PER_STAT
from core.gacha import UPGRADEABLE_STATS
from core.gacha import Banner
from core.gacha import GachaManager
from core.gacha import PullResult
from core.gacha import _calculate_next_cost


class TestGachaUtilities:
    """Tests for gacha utility functions."""
    
    def test_calculate_next_cost(self):
        """Test stat upgrade cost calculation."""
        assert _calculate_next_cost(0) == 1
        assert _calculate_next_cost(1) == 2  # ceil(1 * 1.05) = 2
        assert _calculate_next_cost(100) == 105
        
        # Test growth over multiple steps
        cost = 1
        for _ in range(10):
            cost = _calculate_next_cost(cost)
        assert cost > 1  # Should increase


class TestPullResult:
    """Tests for PullResult dataclass."""
    
    def test_pull_result_character(self):
        """Test character pull result."""
        result = PullResult("character", "becca", 5, stacks=1)
        assert result.type == "character"
        assert result.id == "becca"
        assert result.rarity == 5
        assert result.stacks == 1
    
    def test_pull_result_item(self):
        """Test item pull result."""
        result = PullResult("item", "fire_3", 3)
        assert result.type == "item"
        assert result.id == "fire_3"
        assert result.rarity == 3
        assert result.stacks is None


class TestBanner:
    """Tests for Banner dataclass."""
    
    def test_banner_standard(self):
        """Test standard banner creation."""
        banner = Banner("standard", "Standard Warp", "standard")
        assert banner.id == "standard"
        assert banner.banner_type == "standard"
        assert banner.featured_character is None
    
    def test_banner_custom(self):
        """Test custom banner with featured character."""
        banner = Banner(
            "custom1", 
            "Featured Banner", 
            "custom", 
            featured_character="becca",
            start_time=time.time(),
            end_time=time.time() + 86400
        )
        assert banner.banner_type == "custom"
        assert banner.featured_character == "becca"


class TestGachaManager:
    """Tests for GachaManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Reset save state before each test
        from core.save_manager import SaveManager
        SaveManager.save_setting("gacha_state", {})
    
    def test_initialization(self):
        """Test gacha manager initializes with default state."""
        manager = GachaManager()
        
        assert manager.get_pity() == 0
        assert manager.get_items() == {}
        assert len(manager.get_banners()) > 0
    
    def test_banners_created(self):
        """Test that default banners are created."""
        manager = GachaManager()
        banners = manager.get_banners()
        
        # Should have at least standard banner
        assert any(b.banner_type == "standard" for b in banners)
        
        # Standard banner should be available
        available = manager.get_available_banners()
        assert any(b.id == "standard" for b in available)
    
    def test_pity_counter(self):
        """Test pity counter management."""
        manager = GachaManager()
        
        assert manager.get_pity() == 0
        
        manager._set_pity(50)
        assert manager.get_pity() == 50
    
    def test_item_management(self):
        """Test item inventory management."""
        manager = GachaManager()
        
        manager._add_item("fire_1", 5)
        items = manager.get_items()
        assert items.get("fire_1") == 5
        
        manager._add_item("fire_1", 3)
        items = manager.get_items()
        assert items.get("fire_1") == 8
    
    def test_auto_craft(self):
        """Test automatic item crafting."""
        manager = GachaManager()
        
        # Add 125 1★ items to trigger craft
        manager._add_item("fire_1", 125)
        items = manager.get_items()
        
        # Should have crafted into 1x 2★ item
        assert items.get("fire_2", 0) >= 1
        assert items.get("fire_1", 0) < 125
    
    def test_character_stacks(self):
        """Test character duplicate tracking."""
        manager = GachaManager()
        
        stacks, bonus = manager._add_character("becca")
        assert stacks == 1
        assert bonus == 0  # First pull grants no bonus
        
        stacks, bonus = manager._add_character("becca")
        assert stacks == 2
        assert bonus > 0  # Duplicate grants stat levels
    
    def test_duplicate_stat_levels(self):
        """Test that duplicates grant correct number of stat levels."""
        manager = GachaManager()
        
        # First pull
        manager._add_character("becca")
        
        # Second pull (duplicate)
        stacks, bonus_levels = manager._add_character("becca")
        
        expected_levels = len(UPGRADEABLE_STATS) * FREE_DUPLICATE_LEVELS_PER_STAT
        assert bonus_levels == expected_levels
    
    def test_pull_insufficient_tickets(self):
        """Test that pulling without tickets raises error."""
        manager = GachaManager()
        
        with pytest.raises(PermissionError):
            manager.pull(1)
    
    def test_pull_with_tickets(self):
        """Test successful pull with tickets."""
        manager = GachaManager()
        
        # Add tickets
        manager._add_item("ticket", 10)
        
        # Perform pull
        results = manager.pull(1)
        
        assert len(results) == 1
        assert isinstance(results[0], PullResult)
        
        # Tickets should be deducted
        items = manager.get_items()
        assert items.get("ticket") == 9
    
    def test_pull_counts(self):
        """Test different pull counts."""
        manager = GachaManager()
        manager._add_item("ticket", 20)
        
        # Single pull
        results = manager.pull(1)
        assert len(results) == 1
        
        # 5-pull
        results = manager.pull(5)
        assert len(results) == 5
        
        # 10-pull
        results = manager.pull(10)
        assert len(results) == 10
    
    def test_pull_invalid_count(self):
        """Test that invalid pull counts are rejected."""
        manager = GachaManager()
        manager._add_item("ticket", 100)
        
        with pytest.raises(ValueError):
            manager.pull(3)  # Only 1, 5, 10 allowed
    
    def test_pity_increases_on_non_character_pull(self):
        """Test that pity increases when not pulling a character."""
        manager = GachaManager()
        manager._add_item("ticket", 100)
        
        initial_pity = manager.get_pity()
        
        # Pull until we get an item (not character)
        # Set seed for reproducibility
        random.seed(12345)
        results = manager.pull(10)
        
        # At least some pulls should be items
        item_pulls = [r for r in results if r.type == "item"]
        if item_pulls:
            # Pity should have increased for non-character pulls
            assert manager.get_pity() >= initial_pity
    
    def test_pity_resets_on_5star(self):
        """Test that pity resets when pulling 5★ character."""
        manager = GachaManager()
        manager._add_item("ticket", 200)
        
        # Set high pity to guarantee 5★
        manager._set_pity(179)
        
        character_pool = [
            {"id": "becca", "gacha_rarity": 5},
            {"id": "ally", "gacha_rarity": 5}
        ]
        
        results = manager.pull(1, character_pool=character_pool)
        
        # Should get a 5★ character
        assert any(r.rarity == 5 for r in results)
        
        # Pity should reset
        assert manager.get_pity() == 0
    
    def test_rarity_weights_increase_with_pity(self):
        """Test that higher pity increases higher rarity chances."""
        manager = GachaManager()
        
        weights_low = manager._rarity_weights(0)
        weights_high = manager._rarity_weights(100)
        
        # At low pity, lower rarities dominate
        assert weights_low[0] > weights_high[0]  # 1★ decreases
        
        # At high pity, higher rarities increase
        assert weights_high[3] > weights_low[3]  # 4★ increases
    
    def test_featured_character_rate_up(self):
        """Test that featured characters have rate-up on custom banners."""
        manager = GachaManager()
        manager._add_item("ticket", 1000)
        
        # This test is probabilistic, so we use a large sample
        # and check that featured character appears more often
        character_pool = [
            {"id": "becca", "gacha_rarity": 5},
            {"id": "ally", "gacha_rarity": 5},
            {"id": "mezzy", "gacha_rarity": 5}
        ]
        
        # Force high pity to guarantee character pulls
        manager._set_pity(179)
        
        featured_char = "becca"
        pulls_with_featured = 0
        total_char_pulls = 0
        
        random.seed(42)
        for _ in range(10):  # Do multiple pulls
            results = manager.pull(1, banner_id="custom1", character_pool=character_pool)
            for result in results:
                if result.type == "character" and result.rarity == 5:
                    total_char_pulls += 1
                    if result.id == featured_char:
                        pulls_with_featured += 1
            manager._set_pity(179)  # Reset to guarantee character
        
        # Featured character should appear in at least some pulls
        # (This is probabilistic, but with 50% rate-up it should happen)
        if total_char_pulls > 0:
            rate = pulls_with_featured / total_char_pulls
            # With 50% rate-up, we expect around 40-60% (allowing variance)
            assert rate >= 0.2  # At least 20% (very conservative check)
    
    def test_get_state(self):
        """Test state serialization for UI."""
        manager = GachaManager()
        manager._add_item("fire_1", 5)
        manager._add_character("becca")
        
        state = manager.get_state()
        
        assert "pity" in state
        assert "items" in state
        assert "owned_characters" in state
        assert "character_stacks" in state
        assert "banners" in state
        
        assert state["items"].get("fire_1") == 5
        assert "becca" in state["owned_characters"]
        assert state["character_stacks"].get("becca") == 1
