"""Tests for relic system."""

from pathlib import Path
import sys

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.effect_manager import EffectManager
from core.relic_manager import RelicManager
from core.relics import Relic
from core.relics import get_relic_registry
from core.relics import instantiate_relic
from core.relics import register_relic
from core.stats import Stats


@register_relic
class TestRelicATK(Relic):
    """Test relic with ATK bonus."""
    def __init__(self):
        super().__init__(
            id="test_relic_1",
            name="Test Relic 1",
            stars=1,
            effects={"atk": 0.25},  # +25% ATK per stack
            full_about="Grants +25% ATK per stack"
        )


@register_relic
class TestRelicDEF(Relic):
    """Test relic with DEF bonus."""
    def __init__(self):
        super().__init__(
            id="test_relic_2",
            name="Test Relic 2",
            stars=2,
            effects={"defense": 0.5},  # +50% DEF per stack
            full_about="Grants +50% DEF per stack"
        )


@register_relic
class TestRelicMulti(Relic):
    """Test relic with multiple effects."""
    def __init__(self):
        super().__init__(
            id="test_relic_3",
            name="Test Relic 3",
            stars=3,
            effects={"atk": 0.1, "spd": 0.2},  # +10% ATK, +20% SPD per stack
            full_about="Grants +10% ATK and +20% SPD per stack"
        )


class TestRelic:
    """Test Relic class functionality."""

    def test_relic_creation(self):
        """Test basic relic creation."""
        relic = TestRelicATK()
        assert relic.id == "test_relic_1"
        assert relic.name == "Test Relic 1"
        assert relic.stars == 1
        assert relic.effects == {"atk": 0.25}

    def test_relic_apply_single_stack(self):
        """Test applying relic with 1 stack."""
        stats = Stats(hp=1000, level=1)
        stats._base_atk = 100
        effect_mgr = EffectManager(stats)

        relic = TestRelicATK()
        relic.apply(stats, effect_mgr, stacks=1)

        # Should have +25% ATK
        assert stats.atk == 125  # 100 * 1.25

    def test_relic_apply_multiple_stacks(self):
        """Test applying relic with multiple stacks."""
        stats = Stats(hp=1000, level=1)
        stats._base_atk = 100
        effect_mgr = EffectManager(stats)

        relic = TestRelicATK()
        relic.apply(stats, effect_mgr, stacks=3)

        # Formula: (1 + 0.25)^3 = 1.953125
        # 100 * 1.953125 ≈ 195
        assert stats.atk == pytest.approx(195, abs=1)

    def test_relic_stacking_formula(self):
        """Test that stacking uses multiplicative formula."""
        stats = Stats(hp=1000, level=1)
        stats._base_atk = 100
        stats._base_defense = 100  # Set base defense to 100
        effect_mgr = EffectManager(stats)

        # Apply 50% bonus with 2 stacks
        # Should be (1.5)^2 = 2.25x, not 2.0x
        relic = TestRelicDEF()
        relic.apply(stats, effect_mgr, stacks=2)

        # 100 defense * 2.25 = 225
        assert stats.defense == 225

    def test_relic_remove(self):
        """Test removing relic effects."""
        stats = Stats(hp=1000, level=1)
        stats._base_atk = 100
        effect_mgr = EffectManager(stats)

        relic = TestRelicATK()
        relic.apply(stats, effect_mgr, stacks=1)
        assert stats.atk == 125

        relic.remove(effect_mgr)
        assert stats.atk == 100  # Back to base

    def test_relic_multiple_effects(self):
        """Test relic with multiple stat effects."""
        stats = Stats(hp=1000, level=1)
        stats._base_atk = 100
        stats._base_spd = 10
        effect_mgr = EffectManager(stats)

        relic = TestRelicMulti()
        relic.apply(stats, effect_mgr, stacks=2)

        # ATK: (1.1)^2 = 1.21 -> 121
        # SPD: (1.2)^2 = 1.44 -> 14.4 ≈ 14
        assert stats.atk == pytest.approx(121, abs=1)
        assert stats.spd == pytest.approx(14, abs=1)

    def test_relic_get_about_str(self):
        """Test getting relic description."""
        relic = TestRelicATK()
        assert relic.get_about_str(stacks=1) == "Grants +25% ATK per stack"


class TestRelicRegistry:
    """Test RelicRegistry functionality."""

    def test_registry_contains_relics(self):
        """Test that registered relics are in registry."""
        registry = get_relic_registry()

        assert registry.get("test_relic_1") is not None
        assert registry.get("test_relic_2") is not None
        assert registry.get("test_relic_3") is not None

    def test_registry_instantiate(self):
        """Test instantiating relics from registry."""
        relic = instantiate_relic("test_relic_1")
        assert relic is not None
        assert relic.id == "test_relic_1"
        assert isinstance(relic, Relic)

    def test_registry_get_by_stars(self):
        """Test getting relics by star rating."""
        registry = get_relic_registry()

        stars_1 = registry.get_by_stars(1)
        stars_2 = registry.get_by_stars(2)
        stars_3 = registry.get_by_stars(3)

        # Check that test relics are in correct star tiers
        assert len(stars_1) >= 1
        assert len(stars_2) >= 1
        assert len(stars_3) >= 1

    def test_registry_get_random_relics(self):
        """Test random relic selection."""
        registry = get_relic_registry()

        # Get random 1-star relics
        relics = registry.get_random_relics(stars=1, count=3)
        assert len(relics) <= 3
        assert all(r.stars == 1 for r in relics)

    def test_registry_get_random_allows_duplicates(self):
        """Test that random selection allows duplicates (stacking)."""
        registry = get_relic_registry()

        # Should not exclude owned relics by default
        relics = registry.get_random_relics(stars=1, count=10, exclude=[])

        # This should work even if some relics are "owned"
        assert len(relics) > 0


class TestRelicManager:
    """Test RelicManager functionality."""

    def test_manager_creation(self):
        """Test creating relic manager."""
        stats = Stats(hp=1000, level=1)
        effect_mgr = EffectManager(stats)
        manager = RelicManager(stats, effect_mgr)

        assert manager.equipped == []
        assert manager.get_total_relic_count() == 0

    def test_add_relic(self):
        """Test adding a relic."""
        stats = Stats(hp=1000, level=1)
        stats._base_atk = 100
        effect_mgr = EffectManager(stats)
        manager = RelicManager(stats, effect_mgr)

        assert manager.add_relic("test_relic_1")
        assert "test_relic_1" in manager.equipped
        assert stats.atk == 125  # +25% applied

    def test_add_relic_stacking(self):
        """Test adding the same relic multiple times."""
        stats = Stats(hp=1000, level=1)
        stats._base_atk = 100
        effect_mgr = EffectManager(stats)
        manager = RelicManager(stats, effect_mgr)

        # Add same relic twice
        manager.add_relic("test_relic_1")
        manager.add_relic("test_relic_1")

        assert manager.get_stack_count("test_relic_1") == 2
        # (1.25)^2 = 1.5625 -> 156
        assert stats.atk == pytest.approx(156, abs=1)

    def test_remove_relic_single_stack(self):
        """Test removing one stack of a relic."""
        stats = Stats(hp=1000, level=1)
        stats._base_atk = 100
        effect_mgr = EffectManager(stats)
        manager = RelicManager(stats, effect_mgr)

        # Add 2 stacks
        manager.add_relic("test_relic_1")
        manager.add_relic("test_relic_1")
        assert manager.get_stack_count("test_relic_1") == 2

        # Remove one
        manager.remove_relic("test_relic_1", remove_all=False)
        assert manager.get_stack_count("test_relic_1") == 1
        assert stats.atk == 125  # Back to 1 stack

    def test_remove_relic_all_stacks(self):
        """Test removing all stacks of a relic."""
        stats = Stats(hp=1000, level=1)
        stats._base_atk = 100
        effect_mgr = EffectManager(stats)
        manager = RelicManager(stats, effect_mgr)

        # Add 3 stacks
        manager.add_relic("test_relic_1")
        manager.add_relic("test_relic_1")
        manager.add_relic("test_relic_1")

        # Remove all
        manager.remove_relic("test_relic_1", remove_all=True)
        assert manager.get_stack_count("test_relic_1") == 0
        assert stats.atk == 100  # Back to base

    def test_get_stack_count(self):
        """Test getting stack count for a relic."""
        stats = Stats(hp=1000, level=1)
        effect_mgr = EffectManager(stats)
        manager = RelicManager(stats, effect_mgr)

        assert manager.get_stack_count("test_relic_1") == 0

        manager.add_relic("test_relic_1")
        assert manager.get_stack_count("test_relic_1") == 1

        manager.add_relic("test_relic_1")
        assert manager.get_stack_count("test_relic_1") == 2

    def test_get_unique_relics(self):
        """Test getting list of unique relics."""
        stats = Stats(hp=1000, level=1)
        effect_mgr = EffectManager(stats)
        manager = RelicManager(stats, effect_mgr)

        manager.add_relic("test_relic_1")
        manager.add_relic("test_relic_1")
        manager.add_relic("test_relic_2")

        unique = manager.get_unique_relics()
        assert len(unique) == 2
        assert set(unique) == {"test_relic_1", "test_relic_2"}

    def test_get_relic_counts(self):
        """Test getting stack counts for all relics."""
        stats = Stats(hp=1000, level=1)
        effect_mgr = EffectManager(stats)
        manager = RelicManager(stats, effect_mgr)

        manager.add_relic("test_relic_1")
        manager.add_relic("test_relic_1")
        manager.add_relic("test_relic_2")

        counts = manager.get_relic_counts()
        assert counts["test_relic_1"] == 2
        assert counts["test_relic_2"] == 1

    def test_reapply_all(self):
        """Test reapplying all relics."""
        stats = Stats(hp=1000, level=1)
        stats._base_atk = 100
        effect_mgr = EffectManager(stats)
        manager = RelicManager(stats, effect_mgr)

        manager.add_relic("test_relic_1")
        initial_atk = stats.atk

        # Manually add to equipped list (simulating external modification)
        manager.equipped.append("test_relic_1")

        # Reapply should update to reflect 2 stacks
        manager.reapply_all()
        assert stats.atk > initial_atk

    def test_has_relic(self):
        """Test checking if a relic is equipped."""
        stats = Stats(hp=1000, level=1)
        effect_mgr = EffectManager(stats)
        manager = RelicManager(stats, effect_mgr)

        assert not manager.has_relic("test_relic_1")

        manager.add_relic("test_relic_1")
        assert manager.has_relic("test_relic_1")

    def test_get_relic_instances(self):
        """Test getting relic instances with stack counts."""
        stats = Stats(hp=1000, level=1)
        effect_mgr = EffectManager(stats)
        manager = RelicManager(stats, effect_mgr)

        manager.add_relic("test_relic_1")
        manager.add_relic("test_relic_1")
        manager.add_relic("test_relic_2")

        instances = manager.get_relic_instances()
        assert len(instances) == 2

        # Check stacks
        for relic, stacks in instances:
            if relic.id == "test_relic_1":
                assert stacks == 2
            elif relic.id == "test_relic_2":
                assert stacks == 1

    def test_clear(self):
        """Test clearing all relics."""
        stats = Stats(hp=1000, level=1)
        stats._base_atk = 100
        effect_mgr = EffectManager(stats)
        manager = RelicManager(stats, effect_mgr)

        manager.add_relic("test_relic_1")
        manager.add_relic("test_relic_2")
        assert stats.atk > 100

        manager.clear()
        assert len(manager.equipped) == 0
        assert stats.atk == 100  # Back to base

    def test_multiple_relics_interaction(self):
        """Test that multiple different relics work together."""
        stats = Stats(hp=1000, level=1)
        stats._base_atk = 100
        stats._base_defense = 100
        effect_mgr = EffectManager(stats)
        manager = RelicManager(stats, effect_mgr)

        # Add different relics
        manager.add_relic("test_relic_1")  # +25% ATK
        manager.add_relic("test_relic_2")  # +50% DEF

        assert stats.atk == 125
        assert stats.defense == 150

    def test_get_total_and_unique_counts(self):
        """Test total vs unique relic counts."""
        stats = Stats(hp=1000, level=1)
        effect_mgr = EffectManager(stats)
        manager = RelicManager(stats, effect_mgr)

        manager.add_relic("test_relic_1")
        manager.add_relic("test_relic_1")
        manager.add_relic("test_relic_2")

        assert manager.get_total_relic_count() == 3
        assert manager.get_unique_relic_count() == 2
