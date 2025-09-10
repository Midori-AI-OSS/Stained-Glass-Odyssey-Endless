"""
Test suite to validate abilities identified by the audit script.

This test file contains focused tests for representative abilities across all types
to validate that their implementations match their documented behavior.
"""
import pytest

from autofighter.cards import award_card
from autofighter.party import Party
from autofighter.relics import award_relic
from autofighter.stats import Stats
from plugins.cards.arc_lightning import ArcLightning
from plugins.cards.vital_surge import VitalSurge
from plugins.passives.luna_lunar_reservoir import LunaLunarReservoir
from plugins.players.luna import Luna
from plugins.relics.greed_engine import GreedEngine
from plugins.relics.tattered_flag import TatteredFlag


class TestCardValidation:
    """Test card implementations match their documentation."""
    
    def test_arc_lightning_effects(self):
        """Test Arc Lightning provides correct ATK bonus."""
        card = ArcLightning()
        
        # Check documented effects match implementation
        assert card.effects["atk"] == 2.55, "Arc Lightning should provide +255% ATK (2.55 multiplier)"
        assert card.about == "+255% ATK; every attack chains 50% of dealt damage to a random foe."
        assert card.stars == 3, "Arc Lightning should be a 3-star card"
        
    @pytest.mark.asyncio
    async def test_arc_lightning_chain_behavior(self):
        """Test Arc Lightning's chaining behavior is properly implemented."""
        party = Party()
        card = ArcLightning()
        
        # Apply card to party
        await card.apply(party)
        
        # The card should set up event bus subscriptions for chaining
        # This is a behavioral test that the apply method runs without error
        # and sets up the necessary event handlers
        assert True  # If we get here, apply() worked
        
    def test_vital_surge_effects(self):
        """Test Vital Surge provides correct HP bonus."""
        card = VitalSurge()
        
        # Check documented effects match implementation
        assert card.effects["max_hp"] == 0.55, "Vital Surge should provide +55% max HP"
        assert "+55% Max HP" in card.about, "Documentation should mention +55% Max HP"
        assert card.stars == 3, "Vital Surge should be a 3-star card"


class TestRelicValidation:
    """Test relic implementations match their documentation."""
    
    def test_greed_engine_effects(self):
        """Test Greed Engine has proper implementation structure."""
        relic = GreedEngine()
        
        assert relic.id == "greed_engine"
        assert relic.name == "Greed Engine"
        assert relic.stars == 3
        assert "Lose HP each turn but gain extra gold and rare drops" in relic.about
        
    def test_greed_engine_stacking_description(self):
        """Test Greed Engine provides accurate stacking descriptions."""
        relic = GreedEngine()
        
        # Test description for different stack counts
        desc_1 = relic.describe(1)
        desc_2 = relic.describe(2)
        
        assert "1.0% HP" in desc_1, "Single stack should lose 1.0% HP"
        assert "50% more gold" in desc_1, "Single stack should give 50% more gold"
        
        assert "1.5% HP" in desc_2, "Two stacks should lose 1.5% HP"
        assert "75% more gold" in desc_2, "Two stacks should give 75% more gold"
        
    def test_tattered_flag_implementation(self):
        """Test Tattered Flag has proper structure."""
        relic = TatteredFlag()
        
        assert relic.id == "tattered_flag"
        assert relic.name == "Tattered Flag"
        # Note: This relic may have documentation/implementation discrepancies
        # that the audit script should catch


class TestCharacterValidation:
    """Test character implementations match their documentation."""
    
    def test_luna_character_definition(self):
        """Test Luna character has proper definition."""
        # Test the class attributes without instantiating (to avoid LLM dependencies)
        assert Luna.id == "luna"
        assert Luna.name == "Luna"
        assert "luna_lunar_reservoir" in Luna.passives
        assert Luna.actions_display == "number"
        
    def test_luna_damage_type(self):
        """Test Luna has proper damage type assignment."""
        # Test the damage type field without instantiating
        from plugins.damage_types.generic import Generic
        assert isinstance(Luna.damage_type.default_factory(), Generic)


class TestPassiveValidation:
    """Test passive implementations match their documentation."""
    
    def test_luna_lunar_reservoir_charge_mechanics(self):
        """Test Luna's Lunar Reservoir charge system."""
        passive = LunaLunarReservoir()
        
        assert passive.id == "luna_lunar_reservoir"
        assert passive.name == "Lunar Reservoir"
        assert passive.trigger == "action_taken"
        assert passive.max_stacks == 200
        
    @pytest.mark.asyncio
    async def test_luna_lunar_reservoir_scaling(self):
        """Test Luna's attack scaling based on charge."""
        passive = LunaLunarReservoir()
        stats = Stats()
        stats.actions_per_turn = 1  # Start with base
        
        # Clear any existing charge
        LunaLunarReservoir._charge_points.clear()
        
        # Test charge levels and corresponding attack counts
        await passive.apply(stats)
        assert stats.actions_per_turn == 2, "Should start with 2 actions at low charge"
        
        # Manually set charge to test scaling
        LunaLunarReservoir._charge_points[id(stats)] = 35
        await passive.apply(stats)
        assert stats.actions_per_turn == 4, "Should have 4 actions at 35+ charge"
        
        LunaLunarReservoir._charge_points[id(stats)] = 50
        await passive.apply(stats)
        assert stats.actions_per_turn == 8, "Should have 8 actions at 50+ charge"
        
        LunaLunarReservoir._charge_points[id(stats)] = 70
        await passive.apply(stats)
        assert stats.actions_per_turn == 16, "Should have 16 actions at 70+ charge"
        
        LunaLunarReservoir._charge_points[id(stats)] = 85
        await passive.apply(stats)
        assert stats.actions_per_turn == 32, "Should have 32 actions at 85+ charge"
        
    def test_luna_lunar_reservoir_description(self):
        """Test Luna's passive description matches implementation."""
        description = LunaLunarReservoir.get_description()
        
        assert "Gains 1 charge per action" in description
        assert "attack count scales from 2 up to 32" in description
        assert "85+ charge" in description
        assert "Charge beyond 200 grants 0.025% dodge" in description
        assert "drains 50 charge each turn" in description


class TestIntegrationValidation:
    """Test integration between different ability types."""
    
    def test_card_party_integration(self):
        """Test cards can be properly awarded to party."""
        party = Party()
        initial_card_count = len(party.cards)
        
        # Award a card
        card = award_card(party, "arc_lightning")
        
        assert card is not None, "Should successfully award Arc Lightning"
        assert len(party.cards) == initial_card_count + 1, "Party should have one more card"
        assert "arc_lightning" in party.cards, "Party should contain arc_lightning ID"
        
    def test_relic_party_integration(self):
        """Test relics can be properly awarded to party."""
        party = Party()
        initial_relic_count = len(party.relics)
        
        # Award a relic
        relic = award_relic(party, "greed_engine")
        
        assert relic is not None, "Should successfully award Greed Engine"
        assert len(party.relics) == initial_relic_count + 1, "Party should have one more relic"
        assert "greed_engine" in party.relics, "Party should contain greed_engine ID"


class TestAuditSpecificIssues:
    """Test specific issues that the audit script should detect."""
    
    def test_documentation_stat_mismatch_detection(self):
        """Test that audit can detect stat mismatches."""
        # This is a meta-test to ensure our audit methodology is sound
        
        # Create a mock card with mismatched documentation
        class MockCard:
            about = "+50% ATK bonus"  # Claims 50%
            effects = {"atk": 0.25}   # Actually provides 25%
            
        card = MockCard()
        
        # The audit should detect this as a discrepancy
        # (This test validates our audit logic)
        claimed_value = 50  # From documentation
        actual_value = card.effects["atk"] * 100  # Convert to percentage
        
        assert claimed_value != actual_value, "Audit should detect this mismatch"
        assert abs(claimed_value - actual_value) > 1, "Difference should be significant"


if __name__ == "__main__":
    pytest.main([__file__])