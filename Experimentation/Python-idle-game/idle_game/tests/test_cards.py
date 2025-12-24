"""Tests for card system."""

from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.card_manager import CardManager
from core.cards import Card
from core.cards import get_card_registry
from core.cards import instantiate_card
from core.cards import register_card
from core.effect_manager import EffectManager
from core.stats import Stats


@register_card
class TestCardATK(Card):
    """Test card with ATK bonus."""
    def __init__(self):
        super().__init__(
            id="test_card_1",
            name="Test Card 1",
            stars=1,
            effects={"atk": 0.5},  # +50% ATK
            full_about="Grants +50% ATK"
        )


@register_card
class TestCardHP(Card):
    """Test card with max HP bonus."""
    def __init__(self):
        super().__init__(
            id="test_card_2",
            name="Test Card 2",
            stars=2,
            effects={"max_hp": 0.3},  # +30% max HP
            full_about="Grants +30% max HP"
        )


@register_card
class TestCardMulti(Card):
    """Test card with multiple effects."""
    def __init__(self):
        super().__init__(
            id="test_card_3",
            name="Test Card 3",
            stars=3,
            effects={"atk": 0.25, "defense": 0.25, "spd": 0.1},
            full_about="Grants +25% ATK, +25% DEF, +10% SPD"
        )


class TestCard:
    """Test Card class functionality."""

    def test_card_creation(self):
        """Test basic card creation."""
        card = TestCardATK()
        assert card.id == "test_card_1"
        assert card.name == "Test Card 1"
        assert card.stars == 1
        assert card.effects == {"atk": 0.5}

    def test_card_apply(self):
        """Test applying card effects to stats."""
        stats = Stats(hp=1000, level=1)
        stats._base_atk = 100
        effect_mgr = EffectManager(stats)

        card = TestCardATK()
        card.apply(stats, effect_mgr)

        # Should have +50% ATK modifier
        assert stats.atk == 150  # 100 * 1.5

    def test_card_apply_max_hp(self):
        """Test that max_hp bonus also heals."""
        stats = Stats(hp=1000, level=1)
        stats._base_max_hp = 1000
        effect_mgr = EffectManager(stats)

        card = TestCardHP()
        card.apply(stats, effect_mgr)

        # Should have +30% max HP and healing
        assert stats.max_hp == 1300  # 1000 * 1.3
        assert stats.hp == 1300  # Should heal to full

    def test_card_multiple_effects(self):
        """Test card with multiple stat effects."""
        stats = Stats(hp=1000, level=1)
        stats._base_atk = 100
        stats._base_defense = 100
        stats._base_spd = 10
        effect_mgr = EffectManager(stats)

        card = TestCardMulti()
        card.apply(stats, effect_mgr)

        # Check all modifiers applied
        assert stats.atk == 125  # 100 * 1.25
        assert stats.defense == 125  # 100 * 1.25
        assert stats.spd == 11  # 10 * 1.1

    def test_card_get_about_str(self):
        """Test getting card description."""
        card = TestCardATK()
        assert card.get_about_str() == "Grants +50% ATK"


class TestCardRegistry:
    """Test CardRegistry functionality."""

    def test_registry_contains_cards(self):
        """Test that registered cards are in registry."""
        registry = get_card_registry()

        assert registry.get("test_card_1") is not None
        assert registry.get("test_card_2") is not None
        assert registry.get("test_card_3") is not None

    def test_registry_instantiate(self):
        """Test instantiating cards from registry."""
        card = instantiate_card("test_card_1")
        assert card is not None
        assert card.id == "test_card_1"
        assert isinstance(card, Card)

    def test_registry_get_by_stars(self):
        """Test getting cards by star rating."""
        registry = get_card_registry()

        stars_1 = registry.get_by_stars(1)
        stars_2 = registry.get_by_stars(2)
        stars_3 = registry.get_by_stars(3)

        # Check that test cards are in correct star tiers
        assert len(stars_1) >= 1
        assert len(stars_2) >= 1
        assert len(stars_3) >= 1

    def test_registry_get_random_cards(self):
        """Test random card selection."""
        registry = get_card_registry()

        # Get random 1-star cards
        cards = registry.get_random_cards(stars=1, count=3)
        assert len(cards) <= 3
        assert all(c.stars == 1 for c in cards)

    def test_registry_get_random_with_exclude(self):
        """Test random selection with exclusions."""
        registry = get_card_registry()

        # Exclude test_card_1
        cards = registry.get_random_cards(stars=1, count=10, exclude=["test_card_1"])

        # Should not include excluded card
        assert all(c.id != "test_card_1" for c in cards)


class TestCardManager:
    """Test CardManager functionality."""

    def test_manager_creation(self):
        """Test creating card manager."""
        stats = Stats(hp=1000, level=1)
        effect_mgr = EffectManager(stats)
        manager = CardManager(stats, effect_mgr)

        assert manager.collection == []
        assert manager.deck == []
        assert manager.hand == []
        assert manager.discard == []

    def test_add_to_collection(self):
        """Test adding cards to collection."""
        stats = Stats(hp=1000, level=1)
        effect_mgr = EffectManager(stats)
        manager = CardManager(stats, effect_mgr)

        assert manager.add_to_collection("test_card_1")
        assert "test_card_1" in manager.collection

        # Should not add duplicate
        assert not manager.add_to_collection("test_card_1")
        assert manager.collection.count("test_card_1") == 1

    def test_build_deck(self):
        """Test building a deck from collection."""
        stats = Stats(hp=1000, level=1)
        effect_mgr = EffectManager(stats)
        manager = CardManager(stats, effect_mgr)

        manager.add_to_collection("test_card_1")
        manager.add_to_collection("test_card_2")
        manager.add_to_collection("test_card_3")

        manager.build_deck()

        assert len(manager.deck) == 3
        assert set(manager.deck) == {"test_card_1", "test_card_2", "test_card_3"}

    def test_draw_cards(self):
        """Test drawing cards from deck."""
        stats = Stats(hp=1000, level=1)
        effect_mgr = EffectManager(stats)
        manager = CardManager(stats, effect_mgr)

        manager.add_to_collection("test_card_1")
        manager.add_to_collection("test_card_2")
        manager.build_deck()

        drawn = manager.draw(2)

        assert len(drawn) == 2
        assert len(manager.hand) == 2
        assert len(manager.deck) == 0

    def test_draw_refills_from_discard(self):
        """Test that drawing refills from discard when deck is empty."""
        stats = Stats(hp=1000, level=1)
        effect_mgr = EffectManager(stats)
        manager = CardManager(stats, effect_mgr)

        manager.add_to_collection("test_card_1")
        manager.build_deck()

        # Draw all cards
        manager.draw(1)
        assert len(manager.hand) == 1
        assert len(manager.deck) == 0

        # Discard the card
        manager.discard_card("test_card_1")
        assert len(manager.hand) == 0
        assert len(manager.discard) == 1

        # Draw again - should reshuffle from discard
        manager.draw(1)
        assert len(manager.hand) == 1
        assert len(manager.deck) == 0
        assert len(manager.discard) == 0

    def test_discard_card(self):
        """Test discarding a card from hand."""
        stats = Stats(hp=1000, level=1)
        effect_mgr = EffectManager(stats)
        manager = CardManager(stats, effect_mgr)

        manager.add_to_collection("test_card_1")
        manager.build_deck()
        manager.draw(1)

        assert manager.discard_card("test_card_1")
        assert len(manager.hand) == 0
        assert len(manager.discard) == 1

    def test_play_card(self):
        """Test playing a card from hand."""
        stats = Stats(hp=1000, level=1)
        stats._base_atk = 100
        effect_mgr = EffectManager(stats)
        manager = CardManager(stats, effect_mgr)

        manager.add_to_collection("test_card_1")
        manager.build_deck()
        manager.draw(1)

        # Play the card
        assert manager.play_card("test_card_1")

        # Card should be in discard, effects applied
        assert len(manager.hand) == 0
        assert len(manager.discard) == 1
        assert stats.atk == 150  # +50% ATK

    def test_apply_permanent_card(self):
        """Test applying a card permanently without hand."""
        stats = Stats(hp=1000, level=1)
        stats._base_atk = 100
        effect_mgr = EffectManager(stats)
        manager = CardManager(stats, effect_mgr)

        # Apply without adding to collection or hand
        assert manager.apply_permanent_card("test_card_1")

        # Effects should be applied
        assert stats.atk == 150

    def test_max_hand_size(self):
        """Test that hand size is limited."""
        stats = Stats(hp=1000, level=1)
        effect_mgr = EffectManager(stats)
        manager = CardManager(stats, effect_mgr)

        # Add enough cards to exceed max hand size
        for i in range(10):
            manager.add_to_collection(f"test_card_{i % 3 + 1}")

        manager.build_deck()
        manager.draw(10)

        # Should only draw up to max_hand_size
        assert len(manager.hand) <= manager.max_hand_size

    def test_clear_hand(self):
        """Test clearing hand to discard."""
        stats = Stats(hp=1000, level=1)
        effect_mgr = EffectManager(stats)
        manager = CardManager(stats, effect_mgr)

        manager.add_to_collection("test_card_1")
        manager.add_to_collection("test_card_2")
        manager.build_deck()
        manager.draw(2)

        manager.clear_hand()

        assert len(manager.hand) == 0
        assert len(manager.discard) == 2

    def test_reset(self):
        """Test resetting manager."""
        stats = Stats(hp=1000, level=1)
        effect_mgr = EffectManager(stats)
        manager = CardManager(stats, effect_mgr)

        manager.add_to_collection("test_card_1")
        manager.build_deck()
        manager.draw(1)

        manager.reset()

        assert len(manager.deck) == 0
        assert len(manager.hand) == 0
        assert len(manager.discard) == 0
        # Collection should remain
        assert len(manager.collection) == 1
