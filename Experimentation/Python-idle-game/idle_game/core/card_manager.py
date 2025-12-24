"""Card manager for deck and hand management.

Manages a character's card collection, deck building, hand management,
and card drawing/playing mechanics.
"""

import logging
import random
from typing import List
from typing import Optional

from .cards import Card
from .cards import instantiate_card
from .effect_manager import EffectManager
from .stats import Stats

log = logging.getLogger(__name__)


class CardManager:
    """Manages card collection, deck, and hand for a character."""

    def __init__(self, stats: Stats, effect_manager: EffectManager):
        """Initialize card manager.

        Args:
            stats: Character stats
            effect_manager: Effect manager for applying card effects
        """
        self.stats = stats
        self.effect_manager = effect_manager

        # Card collection (owned cards by ID)
        self.collection: List[str] = []

        # Current deck (card IDs to draw from)
        self.deck: List[str] = []

        # Cards in hand (card IDs)
        self.hand: List[str] = []

        # Discard pile (card IDs)
        self.discard: List[str] = []

        # Maximum hand size
        self.max_hand_size: int = 5

    def add_to_collection(self, card_id: str) -> bool:
        """Add a card to the collection.

        Args:
            card_id: Card ID to add

        Returns:
            True if added, False if already owned
        """
        if card_id in self.collection:
            log.warning("Card %s already in collection", card_id)
            return False

        self.collection.append(card_id)
        log.info("Added card %s to collection", card_id)
        return True

    def remove_from_collection(self, card_id: str) -> bool:
        """Remove a card from the collection.

        Args:
            card_id: Card ID to remove

        Returns:
            True if removed, False if not found
        """
        if card_id not in self.collection:
            log.warning("Card %s not in collection", card_id)
            return False

        self.collection.remove(card_id)
        log.info("Removed card %s from collection", card_id)
        return True

    def build_deck(self, card_ids: Optional[List[str]] = None) -> None:
        """Build a deck from card IDs.

        If no IDs provided, uses all cards in collection.

        Args:
            card_ids: List of card IDs to include in deck
        """
        if card_ids is None:
            card_ids = self.collection.copy()

        # Validate all cards are in collection
        invalid = [cid for cid in card_ids if cid not in self.collection]
        if invalid:
            log.warning("Invalid card IDs for deck: %s", invalid)
            card_ids = [cid for cid in card_ids if cid in self.collection]

        self.deck = card_ids.copy()
        self.hand.clear()
        self.discard.clear()

        # Shuffle deck
        random.shuffle(self.deck)
        log.info("Built deck with %d cards", len(self.deck))

    def draw(self, count: int = 1) -> List[str]:
        """Draw cards from deck to hand.

        If deck is empty, shuffles discard pile back into deck.

        Args:
            count: Number of cards to draw

        Returns:
            List of drawn card IDs
        """
        drawn = []

        for _ in range(count):
            # Check if hand is full
            if len(self.hand) >= self.max_hand_size:
                log.debug("Hand is full, cannot draw more cards")
                break

            # Refill deck if empty
            if not self.deck:
                if self.discard:
                    log.info("Deck empty, shuffling discard pile")
                    self.deck = self.discard.copy()
                    self.discard.clear()
                    random.shuffle(self.deck)
                else:
                    log.debug("Deck and discard empty, cannot draw")
                    break

            # Draw card
            card_id = self.deck.pop(0)
            self.hand.append(card_id)
            drawn.append(card_id)
            log.debug("Drew card: %s", card_id)

        return drawn

    def discard_card(self, card_id: str) -> bool:
        """Discard a card from hand.

        Args:
            card_id: Card ID to discard

        Returns:
            True if discarded, False if not in hand
        """
        if card_id not in self.hand:
            log.warning("Card %s not in hand", card_id)
            return False

        self.hand.remove(card_id)
        self.discard.append(card_id)
        log.debug("Discarded card: %s", card_id)
        return True

    def play_card(self, card_id: str) -> bool:
        """Play a card from hand.

        Applies the card's effects and moves it to discard.

        Args:
            card_id: Card ID to play

        Returns:
            True if played successfully, False otherwise
        """
        if card_id not in self.hand:
            log.warning("Card %s not in hand", card_id)
            return False

        # Instantiate and apply card
        card = instantiate_card(card_id)
        if card is None:
            log.error("Failed to instantiate card: %s", card_id)
            return False

        try:
            card.apply(self.stats, self.effect_manager)

            # Move to discard
            self.hand.remove(card_id)
            self.discard.append(card_id)

            log.info("Played card: %s", card_id)
            return True

        except Exception as e:
            log.error("Error playing card %s: %s", card_id, e)
            return False

    def apply_permanent_card(self, card_id: str) -> bool:
        """Apply a card's effects permanently (not from hand).

        Used for cards that are awarded and applied immediately,
        not drawn/played during combat.

        Args:
            card_id: Card ID to apply

        Returns:
            True if applied successfully
        """
        card = instantiate_card(card_id)
        if card is None:
            log.error("Failed to instantiate card: %s", card_id)
            return False

        try:
            card.apply(self.stats, self.effect_manager)
            log.info("Applied permanent card: %s", card_id)
            return True
        except Exception as e:
            log.error("Error applying card %s: %s", card_id, e)
            return False

    def get_hand_cards(self) -> List[Card]:
        """Get card instances for cards in hand.

        Returns:
            List of card instances
        """
        cards = []
        for card_id in self.hand:
            card = instantiate_card(card_id)
            if card:
                cards.append(card)
        return cards

    def shuffle_deck(self) -> None:
        """Shuffle the current deck."""
        random.shuffle(self.deck)
        log.debug("Shuffled deck")

    def clear_hand(self) -> None:
        """Discard all cards in hand."""
        self.discard.extend(self.hand)
        self.hand.clear()
        log.debug("Cleared hand to discard")

    def reset(self) -> None:
        """Reset deck, hand, and discard."""
        self.deck.clear()
        self.hand.clear()
        self.discard.clear()
        log.info("Reset card manager")
