"""
Base room classes for the idle game.
Simplified from backend/autofighter/rooms/.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class RoomResult(Enum):
    """Result of completing a room."""
    VICTORY = "victory"
    DEFEAT = "defeat"
    FLED = "fled"
    CONTINUE = "continue"
    SKIPPED = "skipped"


@dataclass
class Room:
    """Base class for all room types."""

    room_id: int
    room_type: str
    floor: int
    loop: int = 1
    pressure: int = 0
    completed: bool = False
    result: RoomResult | None = None
    rewards: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "room_id": self.room_id,
            "room_type": self.room_type,
            "floor": self.floor,
            "loop": self.loop,
            "pressure": self.pressure,
            "completed": self.completed,
            "result": self.result.value if self.result else None,
            "rewards": self.rewards or {},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Room:
        """Create from dictionary."""
        result_str = data.get("result")
        result = RoomResult(result_str) if result_str else None

        return cls(
            room_id=data.get("room_id", 0),
            room_type=data.get("room_type", "battle-weak"),
            floor=data.get("floor", 1),
            loop=data.get("loop", 1),
            pressure=data.get("pressure", 0),
            completed=data.get("completed", False),
            result=result,
            rewards=data.get("rewards"),
        )

    def is_battle(self) -> bool:
        """Check if this is a battle room."""
        return self.room_type.startswith("battle")

    def is_shop(self) -> bool:
        """Check if this is a shop room."""
        return self.room_type == "shop"

    def is_rest(self) -> bool:
        """Check if this is a rest room."""
        return self.room_type == "rest"

    def is_boss(self) -> bool:
        """Check if this is a boss battle."""
        return "boss" in self.room_type


@dataclass
class BattleRoom(Room):
    """Battle room with enemy information."""

    enemy_ids: list[str] | None = None
    enemy_count: int = 0
    difficulty: str = "normal"  # weak, normal, elite, prime, boss

    def __post_init__(self):
        """Initialize battle-specific fields."""
        if not self.enemy_ids:
            self.enemy_ids = []

        # Determine difficulty from room type
        if "weak" in self.room_type:
            self.difficulty = "weak"
        elif "elite" in self.room_type:
            self.difficulty = "elite"
        elif "prime" in self.room_type:
            self.difficulty = "prime"
        elif "boss" in self.room_type:
            self.difficulty = "boss"
        else:
            self.difficulty = "normal"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = super().to_dict()
        data.update({
            "enemy_ids": self.enemy_ids or [],
            "enemy_count": self.enemy_count,
            "difficulty": self.difficulty,
        })
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BattleRoom:
        """Create from dictionary."""
        result_str = data.get("result")
        result = RoomResult(result_str) if result_str else None

        return cls(
            room_id=data.get("room_id", 0),
            room_type=data.get("room_type", "battle-weak"),
            floor=data.get("floor", 1),
            loop=data.get("loop", 1),
            pressure=data.get("pressure", 0),
            completed=data.get("completed", False),
            result=result,
            rewards=data.get("rewards"),
            enemy_ids=data.get("enemy_ids", []),
            enemy_count=data.get("enemy_count", 0),
            difficulty=data.get("difficulty", "normal"),
        )


@dataclass
class ShopRoom(Room):
    """Shop room with purchasable items."""

    items_available: list[dict[str, Any]] | None = None
    items_purchased: list[str] | None = None

    def __post_init__(self):
        """Initialize shop-specific fields."""
        if not self.items_available:
            self.items_available = []
        if not self.items_purchased:
            self.items_purchased = []

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = super().to_dict()
        data.update({
            "items_available": self.items_available or [],
            "items_purchased": self.items_purchased or [],
        })
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ShopRoom:
        """Create from dictionary."""
        result_str = data.get("result")
        result = RoomResult(result_str) if result_str else None

        return cls(
            room_id=data.get("room_id", 0),
            room_type=data.get("room_type", "shop"),
            floor=data.get("floor", 1),
            loop=data.get("loop", 1),
            pressure=data.get("pressure", 0),
            completed=data.get("completed", False),
            result=result,
            rewards=data.get("rewards"),
            items_available=data.get("items_available", []),
            items_purchased=data.get("items_purchased", []),
        )


@dataclass
class RestRoom(Room):
    """Rest room for healing and recovery."""

    heal_amount: int = 0
    heal_percentage: float = 0.5  # Heal 50% by default

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = super().to_dict()
        data.update({
            "heal_amount": self.heal_amount,
            "heal_percentage": self.heal_percentage,
        })
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RestRoom:
        """Create from dictionary."""
        result_str = data.get("result")
        result = RoomResult(result_str) if result_str else None

        return cls(
            room_id=data.get("room_id", 0),
            room_type=data.get("room_type", "rest"),
            floor=data.get("floor", 1),
            loop=data.get("loop", 1),
            pressure=data.get("pressure", 0),
            completed=data.get("completed", False),
            result=result,
            rewards=data.get("rewards"),
            heal_amount=data.get("heal_amount", 0),
            heal_percentage=data.get("heal_percentage", 0.5),
        )
