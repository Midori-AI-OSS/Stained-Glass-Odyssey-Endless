"""Unit tests for Party system."""

import sys
from pathlib import Path

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.party import Party


class TestParty:
    """Tests for Party class."""
    
    def test_party_initialization(self):
        """Test party starts empty with default values."""
        party = Party()
        assert party.members == []
        assert party.gold == 0
        assert party.relics == []
        assert party.cards == []
        assert party.rdr == 1.0
        assert not party.no_shops
        assert not party.no_rests
    
    def test_add_member(self):
        """Test adding members to party."""
        party = Party()
        
        assert party.add_member("char1")
        assert "char1" in party.members
        assert len(party.members) == 1
    
    def test_add_duplicate_member(self):
        """Test that duplicate members are rejected."""
        party = Party()
        party.add_member("char1")
        
        assert not party.add_member("char1")
        assert len(party.members) == 1
    
    def test_party_size_limit(self):
        """Test that party is limited to 4 members."""
        party = Party()
        
        assert party.add_member("char1")
        assert party.add_member("char2")
        assert party.add_member("char3")
        assert party.add_member("char4")
        assert not party.add_member("char5")
        
        assert len(party.members) == 4
        assert party.is_full()
    
    def test_remove_member(self):
        """Test removing members from party."""
        party = Party()
        party.add_member("char1")
        party.add_member("char2")
        
        assert party.remove_member("char1")
        assert "char1" not in party.members
        assert len(party.members) == 1
    
    def test_remove_nonexistent_member(self):
        """Test removing member not in party."""
        party = Party()
        assert not party.remove_member("char1")
    
    def test_clear_party(self):
        """Test clearing all members."""
        party = Party()
        party.add_member("char1")
        party.add_member("char2")
        
        party.clear()
        assert len(party.members) == 0
        assert party.is_empty()
    
    def test_has_member(self):
        """Test member presence checking."""
        party = Party()
        party.add_member("char1")
        
        assert party.has_member("char1")
        assert not party.has_member("char2")
    
    def test_gold_operations(self):
        """Test gold management."""
        party = Party()
        
        party.add_gold(100)
        assert party.gold == 100
        
        assert party.spend_gold(50)
        assert party.gold == 50
        
        assert not party.spend_gold(100)  # Insufficient gold
        assert party.gold == 50
    
    def test_negative_gold(self):
        """Test that negative gold is prevented."""
        party = Party()
        party.add_gold(-50)
        assert party.gold == 0
    
    def test_relic_operations(self):
        """Test relic management."""
        party = Party()
        
        party.add_relic("relic1")
        assert "relic1" in party.relics
        assert party.has_relic("relic1")
        
        # Adding duplicate relic doesn't duplicate it
        party.add_relic("relic1")
        assert party.relics.count("relic1") == 1
        
        assert party.remove_relic("relic1")
        assert not party.has_relic("relic1")
    
    def test_card_operations(self):
        """Test card management."""
        party = Party()
        
        party.add_card("card1")
        assert "card1" in party.cards
        assert party.has_card("card1")
        
        # Cards can have duplicates
        party.add_card("card1")
        assert party.cards.count("card1") == 2
        
        assert party.remove_card("card1")
        assert party.cards.count("card1") == 1
    
    def test_relic_persistent_state(self):
        """Test relic state persistence."""
        party = Party()
        party.add_relic("relic1")
        party.relic_persistent_state["relic1"] = {"charges": 3}
        
        assert party.relic_persistent_state["relic1"]["charges"] == 3
        
        # State is cleaned up when relic is removed
        party.remove_relic("relic1")
        assert "relic1" not in party.relic_persistent_state
    
    def test_to_dict(self):
        """Test serialization to dictionary."""
        party = Party()
        party.add_member("char1")
        party.gold = 100
        party.add_relic("relic1")
        
        data = party.to_dict()
        
        assert data["members"] == ["char1"]
        assert data["gold"] == 100
        assert data["relics"] == ["relic1"]
        assert "rdr" in data
    
    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "members": ["char1", "char2"],
            "gold": 200,
            "relics": ["relic1"],
            "cards": ["card1", "card2"],
            "rdr": 1.5,
            "no_shops": True,
            "no_rests": False,
            "relic_persistent_state": {"relic1": {"data": "test"}}
        }
        
        party = Party.from_dict(data)
        
        assert party.members == ["char1", "char2"]
        assert party.gold == 200
        assert party.relics == ["relic1"]
        assert party.cards == ["card1", "card2"]
        assert party.rdr == 1.5
        assert party.no_shops
        assert not party.no_rests
        assert party.relic_persistent_state["relic1"]["data"] == "test"
    
    def test_round_trip_serialization(self):
        """Test that serialization and deserialization preserve data."""
        party1 = Party()
        party1.add_member("char1")
        party1.add_member("char2")
        party1.gold = 150
        party1.add_relic("relic1")
        party1.add_card("card1")
        
        data = party1.to_dict()
        party2 = Party.from_dict(data)
        
        assert party2.members == party1.members
        assert party2.gold == party1.gold
        assert party2.relics == party1.relics
        assert party2.cards == party1.cards
