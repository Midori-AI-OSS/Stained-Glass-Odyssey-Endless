"""Tests for rooms system."""

import sys
from pathlib import Path

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.rooms.base import BattleRoom, RestRoom, Room, RoomResult, ShopRoom


class TestRoom:
    """Test basic Room class."""
    
    def test_create_room(self):
        """Test creating a room."""
        room = Room(
            room_id=0,
            room_type="start",
            floor=1,
        )
        
        assert room.room_id == 0
        assert room.room_type == "start"
        assert room.floor == 1
        assert not room.completed
    
    def test_room_to_dict(self):
        """Test converting room to dict."""
        room = Room(
            room_id=1,
            room_type="battle-normal",
            floor=2,
            completed=True,
            result=RoomResult.VICTORY,
        )
        
        data = room.to_dict()
        
        assert data["room_id"] == 1
        assert data["room_type"] == "battle-normal"
        assert data["completed"] is True
        assert data["result"] == "victory"
    
    def test_room_from_dict(self):
        """Test creating room from dict."""
        data = {
            "room_id": 2,
            "room_type": "shop",
            "floor": 3,
            "completed": True,
            "result": "skipped",
        }
        
        room = Room.from_dict(data)
        
        assert room.room_id == 2
        assert room.room_type == "shop"
        assert room.completed is True
        assert room.result == RoomResult.SKIPPED
    
    def test_is_battle(self):
        """Test is_battle method."""
        battle_room = Room(room_id=0, room_type="battle-normal", floor=1)
        shop_room = Room(room_id=1, room_type="shop", floor=1)
        
        assert battle_room.is_battle()
        assert not shop_room.is_battle()
    
    def test_is_shop(self):
        """Test is_shop method."""
        shop_room = Room(room_id=0, room_type="shop", floor=1)
        battle_room = Room(room_id=1, room_type="battle-normal", floor=1)
        
        assert shop_room.is_shop()
        assert not battle_room.is_shop()
    
    def test_is_boss(self):
        """Test is_boss method."""
        boss_room = Room(room_id=0, room_type="battle-boss", floor=1)
        normal_room = Room(room_id=1, room_type="battle-normal", floor=1)
        
        assert boss_room.is_boss()
        assert not normal_room.is_boss()


class TestBattleRoom:
    """Test BattleRoom class."""
    
    def test_create_battle_room(self):
        """Test creating a battle room."""
        room = BattleRoom(
            room_id=0,
            room_type="battle-normal",
            floor=1,
        )
        
        assert room.room_id == 0
        assert room.difficulty == "normal"
        assert room.enemy_ids == []
    
    def test_difficulty_from_room_type(self):
        """Test that difficulty is determined from room type."""
        weak = BattleRoom(room_id=0, room_type="battle-weak", floor=1)
        assert weak.difficulty == "weak"
        
        normal = BattleRoom(room_id=1, room_type="battle-normal", floor=1)
        assert normal.difficulty == "normal"
        
        elite = BattleRoom(room_id=2, room_type="battle-elite", floor=1)
        assert elite.difficulty == "elite"
        
        prime = BattleRoom(room_id=3, room_type="battle-prime", floor=1)
        assert prime.difficulty == "prime"
        
        boss = BattleRoom(room_id=4, room_type="battle-boss", floor=1)
        assert boss.difficulty == "boss"
    
    def test_battle_room_to_dict(self):
        """Test converting battle room to dict."""
        room = BattleRoom(
            room_id=0,
            room_type="battle-elite",
            floor=2,
            enemy_ids=["goblin_1", "goblin_2"],
            enemy_count=2,
        )
        
        data = room.to_dict()
        
        assert data["room_id"] == 0
        assert data["difficulty"] == "elite"
        assert data["enemy_ids"] == ["goblin_1", "goblin_2"]
        assert data["enemy_count"] == 2
    
    def test_battle_room_from_dict(self):
        """Test creating battle room from dict."""
        data = {
            "room_id": 5,
            "room_type": "battle-boss",
            "floor": 3,
            "enemy_ids": ["dragon_boss"],
            "enemy_count": 1,
            "difficulty": "boss",
        }
        
        room = BattleRoom.from_dict(data)
        
        assert room.room_id == 5
        assert room.difficulty == "boss"
        assert room.enemy_ids == ["dragon_boss"]


class TestShopRoom:
    """Test ShopRoom class."""
    
    def test_create_shop_room(self):
        """Test creating a shop room."""
        room = ShopRoom(
            room_id=0,
            room_type="shop",
            floor=1,
        )
        
        assert room.room_id == 0
        assert room.room_type == "shop"
        assert room.items_available == []
        assert room.items_purchased == []
    
    def test_shop_room_with_items(self):
        """Test shop room with items."""
        items = [
            {"type": "card", "price": 50},
            {"type": "relic", "price": 100},
        ]
        
        room = ShopRoom(
            room_id=0,
            room_type="shop",
            floor=1,
            items_available=items,
        )
        
        assert len(room.items_available) == 2
        assert room.items_available[0]["price"] == 50
    
    def test_shop_room_to_dict(self):
        """Test converting shop room to dict."""
        room = ShopRoom(
            room_id=0,
            room_type="shop",
            floor=1,
            items_available=[{"type": "card", "price": 50}],
            items_purchased=["relic_1"],
        )
        
        data = room.to_dict()
        
        assert data["room_id"] == 0
        assert len(data["items_available"]) == 1
        assert data["items_purchased"] == ["relic_1"]
    
    def test_shop_room_from_dict(self):
        """Test creating shop room from dict."""
        data = {
            "room_id": 3,
            "room_type": "shop",
            "floor": 2,
            "items_available": [{"type": "card", "price": 50}],
            "items_purchased": ["card_1"],
        }
        
        room = ShopRoom.from_dict(data)
        
        assert room.room_id == 3
        assert len(room.items_available) == 1
        assert room.items_purchased == ["card_1"]


class TestRestRoom:
    """Test RestRoom class."""
    
    def test_create_rest_room(self):
        """Test creating a rest room."""
        room = RestRoom(
            room_id=0,
            room_type="rest",
            floor=1,
        )
        
        assert room.room_id == 0
        assert room.room_type == "rest"
        assert room.heal_percentage == 0.5
    
    def test_rest_room_healing(self):
        """Test rest room with custom healing."""
        room = RestRoom(
            room_id=0,
            room_type="rest",
            floor=1,
            heal_amount=100,
            heal_percentage=0.75,
        )
        
        assert room.heal_amount == 100
        assert room.heal_percentage == 0.75
    
    def test_rest_room_to_dict(self):
        """Test converting rest room to dict."""
        room = RestRoom(
            room_id=0,
            room_type="rest",
            floor=1,
            heal_amount=150,
            heal_percentage=0.6,
        )
        
        data = room.to_dict()
        
        assert data["room_id"] == 0
        assert data["heal_amount"] == 150
        assert data["heal_percentage"] == 0.6
    
    def test_rest_room_from_dict(self):
        """Test creating rest room from dict."""
        data = {
            "room_id": 4,
            "room_type": "rest",
            "floor": 3,
            "heal_amount": 200,
            "heal_percentage": 0.8,
        }
        
        room = RestRoom.from_dict(data)
        
        assert room.room_id == 4
        assert room.heal_amount == 200
        assert room.heal_percentage == 0.8
