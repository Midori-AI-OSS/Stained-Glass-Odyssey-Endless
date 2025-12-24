"""Party management system for idle game.

This module defines the Party dataclass which holds party composition,
resources (gold), and collected items (relics, cards).
Ported from backend/autofighter/party.py with adaptations for idle game.
"""

from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import Dict
from typing import List


@dataclass
class Party:
    """Represents a party of characters with shared resources.

    Attributes:
        members: List of character IDs in the party (max 4)
        gold: Party's gold/currency amount
        relics: List of relic IDs equipped by the party
        cards: List of card IDs available to the party
        rdr: Risk/reward difficulty multiplier
        no_shops: Whether shops are disabled
        no_rests: Whether rest areas are disabled
        relic_persistent_state: State storage for relics that need persistence
    """

    members: List[str] = field(default_factory=list)
    gold: int = 0
    relics: List[str] = field(default_factory=list)
    cards: List[str] = field(default_factory=list)
    rdr: float = 1.0
    no_shops: bool = False
    no_rests: bool = False
    relic_persistent_state: Dict[str, Any] = field(default_factory=dict)

    def add_member(self, character_id: str) -> bool:
        """Add a character to the party.

        Args:
            character_id: ID of the character to add

        Returns:
            True if added successfully, False if party is full or char already in party
        """
        if len(self.members) >= 4:
            return False
        if character_id in self.members:
            return False
        self.members.append(character_id)
        return True

    def remove_member(self, character_id: str) -> bool:
        """Remove a character from the party.

        Args:
            character_id: ID of the character to remove

        Returns:
            True if removed successfully, False if character not in party
        """
        if character_id not in self.members:
            return False
        self.members.remove(character_id)
        return True

    def is_full(self) -> bool:
        """Check if party is at maximum capacity (4 members)."""
        return len(self.members) >= 4

    def is_empty(self) -> bool:
        """Check if party has no members."""
        return len(self.members) == 0

    def clear(self) -> None:
        """Remove all members from the party."""
        self.members.clear()

    def has_member(self, character_id: str) -> bool:
        """Check if a character is in the party."""
        return character_id in self.members

    def add_gold(self, amount: int) -> None:
        """Add gold to the party's treasury."""
        self.gold = max(0, self.gold + amount)

    def spend_gold(self, amount: int) -> bool:
        """Attempt to spend gold.

        Args:
            amount: Amount of gold to spend

        Returns:
            True if successful, False if insufficient gold
        """
        if self.gold < amount:
            return False
        self.gold -= amount
        return True

    def add_relic(self, relic_id: str) -> None:
        """Add a relic to the party's collection."""
        if relic_id not in self.relics:
            self.relics.append(relic_id)

    def remove_relic(self, relic_id: str) -> bool:
        """Remove a relic from the party.

        Args:
            relic_id: ID of the relic to remove

        Returns:
            True if removed, False if relic not found
        """
        if relic_id in self.relics:
            self.relics.remove(relic_id)
            # Clean up persistent state for this relic
            if relic_id in self.relic_persistent_state:
                del self.relic_persistent_state[relic_id]
            return True
        return False

    def has_relic(self, relic_id: str) -> bool:
        """Check if party has a specific relic."""
        return relic_id in self.relics

    def add_card(self, card_id: str) -> None:
        """Add a card to the party's deck."""
        self.cards.append(card_id)

    def remove_card(self, card_id: str) -> bool:
        """Remove a card from the party's deck.

        Args:
            card_id: ID of the card to remove

        Returns:
            True if removed, False if card not found
        """
        if card_id in self.cards:
            self.cards.remove(card_id)
            return True
        return False

    def has_card(self, card_id: str) -> bool:
        """Check if party has a specific card."""
        return card_id in self.cards

    def to_dict(self) -> Dict[str, Any]:
        """Serialize party to dictionary for saving."""
        return {
            "members": self.members.copy(),
            "gold": self.gold,
            "relics": self.relics.copy(),
            "cards": self.cards.copy(),
            "rdr": self.rdr,
            "no_shops": self.no_shops,
            "no_rests": self.no_rests,
            "relic_persistent_state": self.relic_persistent_state.copy(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Party":
        """Deserialize party from dictionary.

        Args:
            data: Dictionary containing party data

        Returns:
            New Party instance with loaded data
        """
        return cls(
            members=data.get("members", []),
            gold=data.get("gold", 0),
            relics=data.get("relics", []),
            cards=data.get("cards", []),
            rdr=data.get("rdr", 1.0),
            no_shops=data.get("no_shops", False),
            no_rests=data.get("no_rests", False),
            relic_persistent_state=data.get("relic_persistent_state", {}),
        )
