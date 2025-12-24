"""Card system for the idle game.

This module provides the Card base class and card registry for managing
character upgrades through cards. Ported from backend with adaptations
for tick-based Qt system (no async/await).
"""

from dataclasses import dataclass
from dataclasses import field
import logging
import random
from typing import Dict
from typing import List
from typing import Optional

from .effect_manager import EffectManager
from .effects import StatModifier
from .stats import Stats

log = logging.getLogger(__name__)


@dataclass
class Card:
    """Base card class representing a permanent character upgrade.

    Cards provide stat bonuses and special effects that are applied
    to characters. Each card has a star rating indicating rarity and power.
    """

    id: str = ""
    name: str = ""
    stars: int = 1
    effects: Dict[str, float] = field(default_factory=dict)
    full_about: str = "Card description missing"
    summarized_about: str = "Card summary missing"

    def apply(self, stats: Stats, effect_manager: EffectManager) -> None:
        """Apply card effects to a character's stats.

        Creates permanent stat modifiers based on the card's effects dict.
        Effect keys map to stat names, values are multiplier bonuses.

        Args:
            stats: Character stats to apply effects to
            effect_manager: Effect manager for the character
        """
        if not self.effects:
            log.debug("Card %s has no effects to apply", self.id)
            return

        log.info("Applying card %s to character", self.id)

        # Build multipliers dict for StatModifier
        # effects like {"atk": 0.5} means +50% ATK -> multiplier 1.5
        multipliers = {stat_name: 1 + value for stat_name, value in self.effects.items()}

        # Create a single stat modifier with all effects
        modifier = StatModifier(
            id=f"{self.id}",
            name=self.name,
            stats=stats,
            multipliers=multipliers,
            turns=-1,  # Permanent (-1 means infinite)
            bypass_diminishing=False
        )

        effect_manager.add_modifier(modifier)
        log.debug("Applied card %s with effects: %s", self.id, self.effects)

        # Special handling for max_hp: also heal for the increase
        if "max_hp" in self.effects:
            heal_amount = int(stats.hp * self.effects["max_hp"])
            if heal_amount > 0:
                stats.heal(heal_amount)
                log.debug("Healed %d HP from max_hp increase", heal_amount)

    def get_about_str(self, concise: bool = False) -> str:
        """Get the card description.

        Args:
            concise: If True, return summarized version

        Returns:
            Card description string
        """
        return self.summarized_about if concise else self.full_about


class CardRegistry:
    """Registry for managing available cards.

    Provides card lookup, random selection, and instantiation.
    """

    def __init__(self):
        self._cards: Dict[str, type[Card]] = {}

    def register(self, card_cls: type[Card]) -> None:
        """Register a card class.

        Args:
            card_cls: Card class to register
        """
        # Create instance to get ID
        instance = card_cls()
        if not instance.id:
            log.warning("Card class %s has no ID, skipping registration", card_cls.__name__)
            return

        self._cards[instance.id] = card_cls
        log.debug("Registered card: %s", instance.id)

    def get(self, card_id: str) -> Optional[type[Card]]:
        """Get card class by ID.

        Args:
            card_id: Card ID to look up

        Returns:
            Card class or None if not found
        """
        return self._cards.get(card_id)

    def instantiate(self, card_id: str) -> Optional[Card]:
        """Create a card instance.

        Args:
            card_id: Card ID to instantiate

        Returns:
            Card instance or None if not found
        """
        card_cls = self.get(card_id)
        if card_cls is None:
            log.warning("Card not found: %s", card_id)
            return None
        return card_cls()

    def get_by_stars(self, stars: int) -> List[type[Card]]:
        """Get all cards with the given star rating.

        Args:
            stars: Star rating to filter by

        Returns:
            List of card classes
        """
        result = []
        for card_cls in self._cards.values():
            instance = card_cls()
            if instance.stars == stars:
                result.append(card_cls)
        return result

    def get_random_cards(
        self,
        stars: int,
        count: int = 3,
        exclude: Optional[List[str]] = None
    ) -> List[Card]:
        """Get random cards for selection.

        Args:
            stars: Star rating to select from
            count: Number of cards to return
            exclude: List of card IDs to exclude (already owned)

        Returns:
            List of card instances
        """
        exclude = exclude or []
        available = [
            card_cls for card_cls in self.get_by_stars(stars)
            if card_cls().id not in exclude
        ]

        if not available:
            log.debug("No cards available for stars=%d", stars)
            return []

        # Sample up to count cards
        k = min(count, len(available))
        selected = random.sample(available, k)
        return [cls() for cls in selected]

    def get_all_ids(self) -> List[str]:
        """Get all registered card IDs.

        Returns:
            List of card IDs
        """
        return list(self._cards.keys())


# Global card registry
_CARD_REGISTRY = CardRegistry()


def register_card(card_cls: type[Card]) -> type[Card]:
    """Decorator to register a card class.

    Usage:
        @register_card
        class MyCard(Card):
            ...

    Args:
        card_cls: Card class to register

    Returns:
        The card class (unchanged)
    """
    _CARD_REGISTRY.register(card_cls)
    return card_cls


def get_card_registry() -> CardRegistry:
    """Get the global card registry.

    Returns:
        Global card registry instance
    """
    return _CARD_REGISTRY


def instantiate_card(card_id: str) -> Optional[Card]:
    """Create a card instance by ID.

    Args:
        card_id: Card ID to instantiate

    Returns:
        Card instance or None if not found
    """
    return _CARD_REGISTRY.instantiate(card_id)


def get_random_cards(
    stars: int,
    count: int = 3,
    exclude: Optional[List[str]] = None
) -> List[Card]:
    """Get random cards for selection.

    Args:
        stars: Star rating to select from
        count: Number of cards to return
        exclude: List of card IDs to exclude

    Returns:
        List of card instances
    """
    return _CARD_REGISTRY.get_random_cards(stars, count, exclude)
