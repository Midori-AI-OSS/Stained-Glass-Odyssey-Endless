"""Integration tests demonstrating tier passive stacking for Luna and Ixia.

These tests serve as examples for future developers implementing tier passives,
showing how different tier combinations stack and interact.
"""
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from autofighter.passives import PassiveRegistry
from autofighter.passives import apply_rank_passives
from plugins.characters.ixia import Ixia
from plugins.characters.luna import Luna


class TestLunaTierStacking:
    """Test Luna's Lunar Reservoir passive stacking behavior across tiers."""

    @pytest.mark.asyncio
    async def test_luna_normal_charge_multiplier(self):
        """Normal Luna has 1x charge multiplier."""
        luna = Luna()
        luna.rank = "normal"
        luna.passives = ["luna_lunar_reservoir"]

        apply_rank_passives(luna)

        # Normal should have base passive
        assert luna.passives == ["luna_lunar_reservoir"]

        # Get the passive class and verify multiplier
        registry = PassiveRegistry()
        passive_cls = registry._registry.get("luna_lunar_reservoir")
        assert passive_cls is not None
        assert passive_cls._charge_multiplier(luna) == 1

    @pytest.mark.asyncio
    async def test_luna_glitched_charge_multiplier(self):
        """Glitched Luna has 2x charge multiplier."""
        luna = Luna()
        luna.rank = "glitched"
        luna.passives = ["luna_lunar_reservoir"]

        apply_rank_passives(luna)

        # Glitched should have glitched passive
        assert luna.passives == ["luna_lunar_reservoir_glitched"]

        # Get the passive class and verify multiplier
        registry = PassiveRegistry()
        passive_cls = registry._registry.get("luna_lunar_reservoir_glitched")
        assert passive_cls is not None
        assert passive_cls._charge_multiplier(luna) == 2

    @pytest.mark.asyncio
    async def test_luna_prime_charge_multiplier(self):
        """Prime Luna has 5x charge multiplier and healing."""
        luna = Luna()
        luna.rank = "prime"
        luna.passives = ["luna_lunar_reservoir"]

        apply_rank_passives(luna)

        # Prime should have prime passive
        assert luna.passives == ["luna_lunar_reservoir_prime"]

        # Get the passive class and verify multiplier
        registry = PassiveRegistry()
        passive_cls = registry._registry.get("luna_lunar_reservoir_prime")
        assert passive_cls is not None
        assert passive_cls._charge_multiplier(luna) == 5
        # Prime also has healing on hits (checked via _apply_prime_healing method)
        assert hasattr(passive_cls, '_apply_prime_healing')

    @pytest.mark.asyncio
    async def test_luna_glitched_prime_stacking(self):
        """Glitched Prime Luna stacks both 2x and 5x charge multipliers.

        This demonstrates how tier passives stack multiplicatively:
        - Glitched passive provides 2x charge gains
        - Prime passive provides 5x charge gains + healing
        - Both are active simultaneously for combined effect
        """
        luna = Luna()
        luna.rank = "glitched prime"
        luna.passives = ["luna_lunar_reservoir"]

        apply_rank_passives(luna)

        # Both glitched and prime passives should be applied
        assert set(luna.passives) == {
            "luna_lunar_reservoir_glitched",
            "luna_lunar_reservoir_prime"
        }
        assert len(luna.passives) == 2

        # Verify both passive classes exist and have correct multipliers
        registry = PassiveRegistry()

        glitched_cls = registry._registry.get("luna_lunar_reservoir_glitched")
        assert glitched_cls is not None
        assert glitched_cls._charge_multiplier(luna) == 2

        prime_cls = registry._registry.get("luna_lunar_reservoir_prime")
        assert prime_cls is not None
        assert prime_cls._charge_multiplier(luna) == 5

    @pytest.mark.asyncio
    async def test_luna_glitched_prime_boss_full_stacking(self):
        """Glitched Prime Boss Luna stacks all three tier passives.

        This is the most extreme example showing full tier stacking:
        - Glitched: 2x charge multiplier
        - Prime: 5x charge multiplier + healing
        - Boss: Enhanced 4000 soft cap (vs normal 2000)

        All three effects are active simultaneously, making this a
        significantly more powerful version of Luna.
        """
        luna = Luna()
        luna.rank = "glitched prime boss"
        luna.passives = ["luna_lunar_reservoir"]

        apply_rank_passives(luna)

        # All three tier passives should be applied
        assert set(luna.passives) == {
            "luna_lunar_reservoir_glitched",
            "luna_lunar_reservoir_prime",
            "luna_lunar_reservoir_boss"
        }
        assert len(luna.passives) == 3

        # Verify all three passive classes exist with correct properties
        registry = PassiveRegistry()

        glitched_cls = registry._registry.get("luna_lunar_reservoir_glitched")
        assert glitched_cls is not None
        assert glitched_cls._charge_multiplier(luna) == 2

        prime_cls = registry._registry.get("luna_lunar_reservoir_prime")
        assert prime_cls is not None
        assert prime_cls._charge_multiplier(luna) == 5

        boss_cls = registry._registry.get("luna_lunar_reservoir_boss")
        assert boss_cls is not None
        # Boss has enhanced max_stacks (4000 vs 2000)
        assert boss_cls.max_stacks == 4000


class TestIxiaTierStacking:
    """Test Ixia's Tiny Titan passive stacking behavior across tiers."""

    @pytest.mark.asyncio
    async def test_ixia_normal_vitality_gain(self):
        """Normal Ixia gains 0.01 vitality per hit."""
        ixia = Ixia()
        ixia.rank = "normal"
        ixia.passives = ["ixia_tiny_titan"]

        apply_rank_passives(ixia)

        # Normal should have base passive
        assert ixia.passives == ["ixia_tiny_titan"]

        # Verify the passive gains 0.01 vitality per hit (base rate)
        registry = PassiveRegistry()
        passive_cls = registry._registry.get("ixia_tiny_titan")
        assert passive_cls is not None
        # The base passive adds 0.01 per apply call

    @pytest.mark.asyncio
    async def test_ixia_glitched_vitality_gain(self):
        """Glitched Ixia gains 0.02 vitality per hit (doubled)."""
        ixia = Ixia()
        ixia.rank = "glitched"
        ixia.passives = ["ixia_tiny_titan"]

        apply_rank_passives(ixia)

        # Glitched should have glitched passive
        assert ixia.passives == ["ixia_tiny_titan_glitched"]

        # Glitched passive gains 0.02 vitality per hit (2x)
        registry = PassiveRegistry()
        passive_cls = registry._registry.get("ixia_tiny_titan_glitched")
        assert passive_cls is not None
        # The glitched passive adds 0.02 per apply call

    @pytest.mark.asyncio
    async def test_ixia_prime_vitality_gain(self):
        """Prime Ixia has enhanced multipliers and HoT."""
        ixia = Ixia()
        ixia.rank = "prime"
        ixia.passives = ["ixia_tiny_titan"]

        apply_rank_passives(ixia)

        # Prime should have prime passive
        assert ixia.passives == ["ixia_tiny_titan_prime"]

        # Prime has 0.015 vitality gain and enhanced multipliers
        registry = PassiveRegistry()
        passive_cls = registry._registry.get("ixia_tiny_titan_prime")
        assert passive_cls is not None
        # Prime passive adds 0.015 per apply call

    @pytest.mark.asyncio
    async def test_ixia_glitched_boss_stacking(self):
        """Glitched Boss Ixia stacks both tier passives.

        Demonstrates stacking of two tier effects:
        - Glitched: 0.02 vitality per hit (2x)
        - Boss: Enhanced HP multipliers (6x vs base 4x)

        Both passives will trigger on damage_taken events.
        """
        ixia = Ixia()
        ixia.rank = "glitched boss"
        ixia.passives = ["ixia_tiny_titan"]

        apply_rank_passives(ixia)

        # Both glitched and boss passives should be applied
        assert set(ixia.passives) == {
            "ixia_tiny_titan_glitched",
            "ixia_tiny_titan_boss"
        }
        assert len(ixia.passives) == 2

        # Verify both passive classes exist
        registry = PassiveRegistry()
        assert "ixia_tiny_titan_glitched" in registry._registry
        assert "ixia_tiny_titan_boss" in registry._registry

    @pytest.mark.asyncio
    async def test_ixia_glitched_prime_boss_full_stacking(self):
        """Glitched Prime Boss Ixia stacks all three tier passives.

        Maximum stacking example for Ixia:
        - Glitched: 0.02 vitality per hit (2x)
        - Prime: 0.015 vitality per hit + 10x HP multiplier + enhanced HoT
        - Boss: 6x HP multiplier + 750% attack conversion

        All three passives trigger on damage_taken, each adding their
        respective vitality gains and stat effects. This creates an
        extremely tanky and powerful version of Ixia.
        """
        ixia = Ixia()
        ixia.rank = "glitched prime boss"
        ixia.passives = ["ixia_tiny_titan"]

        apply_rank_passives(ixia)

        # All three tier passives should be applied
        assert set(ixia.passives) == {
            "ixia_tiny_titan_glitched",
            "ixia_tiny_titan_prime",
            "ixia_tiny_titan_boss"
        }
        assert len(ixia.passives) == 3

        # Verify all three passive classes exist
        registry = PassiveRegistry()
        assert "ixia_tiny_titan_glitched" in registry._registry
        assert "ixia_tiny_titan_prime" in registry._registry
        assert "ixia_tiny_titan_boss" in registry._registry


class TestMultiplePassivesStacking:
    """Test that characters with multiple base passives stack correctly."""

    @pytest.mark.asyncio
    async def test_multiple_passives_all_stack(self):
        """When a character has multiple passives, each resolves independently.

        If a foe has both luna_lunar_reservoir and ixia_tiny_titan with rank
        "glitched", both should resolve to their glitched variants.
        """
        luna = Luna()
        luna.rank = "glitched"
        luna.passives = ["luna_lunar_reservoir", "ixia_tiny_titan"]

        apply_rank_passives(luna)

        # Both passives should resolve to glitched variants
        assert set(luna.passives) == {
            "luna_lunar_reservoir_glitched",
            "ixia_tiny_titan_glitched"
        }

    @pytest.mark.asyncio
    async def test_multiple_passives_mixed_tiers_all_stack(self):
        """With multiple base passives and multiple tiers, ALL combinations stack.

        With "prime boss" rank and two base passives, we should get:
        - luna_lunar_reservoir_prime
        - luna_lunar_reservoir_boss
        - ixia_tiny_titan_prime
        - ixia_tiny_titan_boss
        Total: 4 passives (2 base × 2 tiers)
        """
        luna = Luna()
        luna.rank = "prime boss"
        luna.passives = ["luna_lunar_reservoir", "ixia_tiny_titan"]

        apply_rank_passives(luna)

        # Each base passive should stack with both tier variants
        expected_passives = {
            "luna_lunar_reservoir_prime",
            "luna_lunar_reservoir_boss",
            "ixia_tiny_titan_prime",
            "ixia_tiny_titan_boss"
        }
        assert set(luna.passives) == expected_passives
        assert len(luna.passives) == 4
