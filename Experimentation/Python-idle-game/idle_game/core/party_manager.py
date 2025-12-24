"""Party management and stat calculation system.

This module provides the PartyManager class which handles party operations,
validation, stat aggregation, and synergy calculations.
"""

from typing import Any
from typing import Dict
from typing import List

from .party import Party


class PartyManager:
    """Manages party composition, validation, and stat calculations.

    Handles party member management, validates party constraints,
    calculates combined party stats, and manages party synergies.
    """

    MAX_PARTY_SIZE = 4

    def __init__(self):
        """Initialize party manager."""
        self.party = Party()

    def get_party(self) -> Party:
        """Get the current party."""
        return self.party

    def set_party(self, party: Party) -> None:
        """Set the current party."""
        self.party = party

    def add_member(
        self,
        character_id: str,
        characters_map: Dict[str, Dict[str, Any]]
    ) -> bool:
        """Add a character to the party with validation.

        Args:
            character_id: ID of character to add
            characters_map: Dictionary of all available characters

        Returns:
            True if added successfully, False otherwise
        """
        # Check if character exists
        if character_id not in characters_map:
            return False

        # Check party size limit
        if self.party.is_full():
            return False

        # Check if already in party
        if self.party.has_member(character_id):
            return False

        return self.party.add_member(character_id)

    def remove_member(self, character_id: str) -> bool:
        """Remove a character from the party.

        Args:
            character_id: ID of character to remove

        Returns:
            True if removed successfully, False if not in party
        """
        return self.party.remove_member(character_id)

    def swap_members(
        self,
        old_character_id: str,
        new_character_id: str,
        characters_map: Dict[str, Dict[str, Any]]
    ) -> bool:
        """Swap one party member for another.

        Args:
            old_character_id: ID of character to remove
            new_character_id: ID of character to add
            characters_map: Dictionary of all available characters

        Returns:
            True if swap successful, False otherwise
        """
        # Validate new character exists
        if new_character_id not in characters_map:
            return False

        # Validate old character is in party
        if not self.party.has_member(old_character_id):
            return False

        # Validate new character not already in party
        if self.party.has_member(new_character_id):
            return False

        # Perform swap
        self.party.remove_member(old_character_id)
        self.party.add_member(new_character_id)
        return True

    def validate_party(
        self,
        characters_map: Dict[str, Dict[str, Any]]
    ) -> tuple[bool, List[str]]:
        """Validate party composition and return any errors.

        Args:
            characters_map: Dictionary of all available characters

        Returns:
            Tuple of (is_valid, list_of_error_messages)
        """
        errors = []

        # Check party size
        if len(self.party.members) > self.MAX_PARTY_SIZE:
            errors.append(f"Party exceeds maximum size of {self.MAX_PARTY_SIZE}")

        # Check for invalid character IDs
        for char_id in self.party.members:
            if char_id not in characters_map:
                errors.append(f"Character '{char_id}' does not exist")

        # Check for duplicates
        if len(self.party.members) != len(set(self.party.members)):
            errors.append("Party contains duplicate characters")

        return len(errors) == 0, errors

    def calculate_party_stats(
        self,
        characters_map: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate combined stats for all party members.

        Args:
            characters_map: Dictionary of all available characters

        Returns:
            Dictionary of aggregated party stats
        """
        if not self.party.members:
            return {
                "total_hp": 0,
                "total_max_hp": 0,
                "total_atk": 0,
                "total_defense": 0,
                "avg_level": 0,
                "total_exp": 0,
                "member_count": 0,
            }

        total_hp = 0
        total_max_hp = 0
        total_atk = 0
        total_defense = 0
        total_level = 0
        total_exp = 0

        for char_id in self.party.members:
            char = characters_map.get(char_id)
            if not char:
                continue

            runtime = char.get("runtime", {})
            base_stats = char.get("base_stats", {})

            total_hp += runtime.get("hp", 0)
            total_max_hp += runtime.get("max_hp", 0)
            total_atk += base_stats.get("atk", 0)
            total_defense += base_stats.get("defense", 0)
            total_level += runtime.get("level", 1)
            total_exp += runtime.get("exp", 0)

        member_count = len(self.party.members)

        return {
            "total_hp": total_hp,
            "total_max_hp": total_max_hp,
            "total_atk": total_atk,
            "total_defense": total_defense,
            "avg_level": total_level / member_count if member_count > 0 else 0,
            "total_exp": total_exp,
            "member_count": member_count,
        }

    def calculate_party_power(
        self,
        characters_map: Dict[str, Dict[str, Any]]
    ) -> float:
        """Calculate overall party power rating.

        Args:
            characters_map: Dictionary of all available characters

        Returns:
            Party power as a float
        """
        stats = self.calculate_party_stats(characters_map)

        # Power formula: weighted combination of stats
        power = (
            stats["total_atk"] * 1.0 +
            stats["total_defense"] * 0.8 +
            stats["total_max_hp"] * 0.1 +
            stats["avg_level"] * 10
        )

        return power

    def get_party_synergies(
        self,
        characters_map: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Calculate synergies between party members.

        Args:
            characters_map: Dictionary of all available characters

        Returns:
            List of synergy effects
        """
        synergies = []

        if not self.party.members:
            return synergies

        # Collect damage types and character types
        damage_types = []
        char_types = []

        for char_id in self.party.members:
            char = characters_map.get(char_id)
            if not char:
                continue

            damage_types.append(char.get("damage_type", "Generic"))
            char_types.append(char.get("char_type", "C"))

        # Check for same damage type synergy (2+ same type)
        from collections import Counter
        damage_counts = Counter(damage_types)
        for dtype, count in damage_counts.items():
            if count >= 2 and dtype != "Generic":
                synergies.append({
                    "type": "elemental_resonance",
                    "element": dtype,
                    "bonus": f"+{count * 5}% {dtype} damage"
                })

        # Check for diverse party bonus (all different damage types)
        if len(set(damage_types)) == len(self.party.members) and len(self.party.members) >= 3:
            synergies.append({
                "type": "elemental_diversity",
                "bonus": "+10% all damage"
            })

        # Check for balanced party (mix of A/B/C types)
        type_counts = Counter(char_types)
        if len(type_counts) >= 2:
            synergies.append({
                "type": "tactical_balance",
                "bonus": "+5% effectiveness"
            })

        return synergies

    def get_party_info(
        self,
        characters_map: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Get comprehensive party information.

        Args:
            characters_map: Dictionary of all available characters

        Returns:
            Dictionary with complete party info
        """
        stats = self.calculate_party_stats(characters_map)
        synergies = self.get_party_synergies(characters_map)
        power = self.calculate_party_power(characters_map)
        is_valid, errors = self.validate_party(characters_map)

        return {
            "members": self.party.members.copy(),
            "stats": stats,
            "synergies": synergies,
            "power": power,
            "is_valid": is_valid,
            "errors": errors,
            "gold": self.party.gold,
            "relic_count": len(self.party.relics),
            "card_count": len(self.party.cards),
        }

    def save_party(self) -> Dict[str, Any]:
        """Serialize party data for saving."""
        return self.party.to_dict()

    def load_party(self, data: Dict[str, Any]) -> None:
        """Load party data from saved state."""
        self.party = Party.from_dict(data)
