"""Unit tests for PartyManager system."""

from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.party_manager import PartyManager


class TestPartyManager:
    """Tests for PartyManager class."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create test character data
        self.characters = {
            "char1": {
                "id": "char1",
                "name": "Character 1",
                "damage_type": "Fire",
                "char_type": "A",
                "base_stats": {
                    "atk": 100,
                    "defense": 80,
                    "max_hp": 1000
                },
                "runtime": {
                    "level": 5,
                    "exp": 200,
                    "hp": 800,
                    "max_hp": 1000
                }
            },
            "char2": {
                "id": "char2",
                "name": "Character 2",
                "damage_type": "Water",
                "char_type": "B",
                "base_stats": {
                    "atk": 120,
                    "defense": 60,
                    "max_hp": 900
                },
                "runtime": {
                    "level": 4,
                    "exp": 150,
                    "hp": 900,
                    "max_hp": 900
                }
            },
            "char3": {
                "id": "char3",
                "name": "Character 3",
                "damage_type": "Fire",
                "char_type": "C",
                "base_stats": {
                    "atk": 90,
                    "defense": 100,
                    "max_hp": 1200
                },
                "runtime": {
                    "level": 6,
                    "exp": 300,
                    "hp": 1200,
                    "max_hp": 1200
                }
            }
        }

    def test_initialization(self):
        """Test party manager initializes with empty party."""
        manager = PartyManager()
        assert manager.get_party() is not None
        assert manager.get_party().is_empty()

    def test_add_member(self):
        """Test adding members with validation."""
        manager = PartyManager()

        assert manager.add_member("char1", self.characters)
        assert manager.get_party().has_member("char1")

    def test_add_nonexistent_member(self):
        """Test that adding nonexistent character fails."""
        manager = PartyManager()
        assert not manager.add_member("invalid", self.characters)

    def test_add_duplicate_member(self):
        """Test that adding duplicate member fails."""
        manager = PartyManager()
        manager.add_member("char1", self.characters)
        assert not manager.add_member("char1", self.characters)

    def test_add_beyond_limit(self):
        """Test that adding beyond 4 members fails."""
        manager = PartyManager()

        # Add a 4th character manually since we only have 3 test chars
        self.characters["char4"] = {
            "id": "char4",
            "base_stats": {"atk": 100, "defense": 100, "max_hp": 1000},
            "runtime": {"level": 1, "exp": 0, "hp": 1000, "max_hp": 1000}
        }

        manager.add_member("char1", self.characters)
        manager.add_member("char2", self.characters)
        manager.add_member("char3", self.characters)
        manager.add_member("char4", self.characters)

        # Try to add 5th member
        self.characters["char5"] = {
            "id": "char5",
            "base_stats": {"atk": 100, "defense": 100, "max_hp": 1000},
            "runtime": {"level": 1, "exp": 0, "hp": 1000, "max_hp": 1000}
        }
        assert not manager.add_member("char5", self.characters)

    def test_remove_member(self):
        """Test removing member."""
        manager = PartyManager()
        manager.add_member("char1", self.characters)

        assert manager.remove_member("char1")
        assert not manager.get_party().has_member("char1")

    def test_swap_members(self):
        """Test swapping party members."""
        manager = PartyManager()
        manager.add_member("char1", self.characters)

        assert manager.swap_members("char1", "char2", self.characters)
        assert not manager.get_party().has_member("char1")
        assert manager.get_party().has_member("char2")

    def test_swap_with_invalid_characters(self):
        """Test swap fails with invalid character IDs."""
        manager = PartyManager()
        manager.add_member("char1", self.characters)

        # Try to swap for nonexistent character
        assert not manager.swap_members("char1", "invalid", self.characters)

        # Try to swap character not in party
        assert not manager.swap_members("char2", "char3", self.characters)

    def test_validate_party(self):
        """Test party validation."""
        manager = PartyManager()
        manager.add_member("char1", self.characters)

        is_valid, errors = manager.validate_party(self.characters)
        assert is_valid
        assert len(errors) == 0

    def test_validate_party_with_invalid_character(self):
        """Test validation catches invalid character IDs."""
        manager = PartyManager()
        manager.get_party().members.append("invalid")

        is_valid, errors = manager.validate_party(self.characters)
        assert not is_valid
        assert len(errors) > 0

    def test_calculate_party_stats(self):
        """Test party stat aggregation."""
        manager = PartyManager()
        manager.add_member("char1", self.characters)
        manager.add_member("char2", self.characters)

        stats = manager.calculate_party_stats(self.characters)

        assert stats["member_count"] == 2
        assert stats["total_atk"] == 220  # 100 + 120
        assert stats["total_defense"] == 140  # 80 + 60
        assert stats["total_hp"] == 1700  # 800 + 900
        assert stats["avg_level"] == 4.5  # (5 + 4) / 2

    def test_calculate_empty_party_stats(self):
        """Test stats calculation for empty party."""
        manager = PartyManager()

        stats = manager.calculate_party_stats(self.characters)

        assert stats["member_count"] == 0
        assert stats["total_atk"] == 0
        assert stats["avg_level"] == 0

    def test_calculate_party_power(self):
        """Test party power calculation."""
        manager = PartyManager()
        manager.add_member("char1", self.characters)
        manager.add_member("char2", self.characters)

        power = manager.calculate_party_power(self.characters)

        assert power > 0
        # Power should increase with more/stronger characters

        manager.add_member("char3", self.characters)
        power_with_three = manager.calculate_party_power(self.characters)
        assert power_with_three > power

    def test_get_party_synergies_same_element(self):
        """Test synergy detection for same element."""
        manager = PartyManager()
        manager.add_member("char1", self.characters)  # Fire
        manager.add_member("char3", self.characters)  # Fire

        synergies = manager.get_party_synergies(self.characters)

        # Should have elemental resonance for Fire
        assert any(s["type"] == "elemental_resonance" for s in synergies)
        fire_synergy = next(s for s in synergies if s["type"] == "elemental_resonance")
        assert fire_synergy["element"] == "Fire"

    def test_get_party_synergies_diversity(self):
        """Test synergy detection for diverse party."""
        # Create characters with different elements
        self.characters["char2"]["damage_type"] = "Water"
        self.characters["char3"]["damage_type"] = "Earth"

        manager = PartyManager()
        manager.add_member("char1", self.characters)  # Fire
        manager.add_member("char2", self.characters)  # Water
        manager.add_member("char3", self.characters)  # Earth

        synergies = manager.get_party_synergies(self.characters)

        # Should have elemental diversity bonus
        assert any(s["type"] == "elemental_diversity" for s in synergies)

    def test_get_party_synergies_balanced_types(self):
        """Test synergy detection for balanced character types."""
        manager = PartyManager()
        manager.add_member("char1", self.characters)  # Type A
        manager.add_member("char2", self.characters)  # Type B

        synergies = manager.get_party_synergies(self.characters)

        # Should have tactical balance bonus
        assert any(s["type"] == "tactical_balance" for s in synergies)

    def test_get_party_info(self):
        """Test comprehensive party info retrieval."""
        manager = PartyManager()
        manager.add_member("char1", self.characters)
        manager.get_party().gold = 500

        info = manager.get_party_info(self.characters)

        assert "members" in info
        assert "stats" in info
        assert "synergies" in info
        assert "power" in info
        assert "is_valid" in info
        assert info["gold"] == 500

    def test_save_and_load_party(self):
        """Test party serialization."""
        manager = PartyManager()
        manager.add_member("char1", self.characters)
        manager.add_member("char2", self.characters)
        manager.get_party().gold = 300

        # Save
        data = manager.save_party()

        # Create new manager and load
        new_manager = PartyManager()
        new_manager.load_party(data)

        # Verify data preserved
        assert new_manager.get_party().has_member("char1")
        assert new_manager.get_party().has_member("char2")
        assert new_manager.get_party().gold == 300
