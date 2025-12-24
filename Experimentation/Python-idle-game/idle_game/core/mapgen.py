"""
Simplified map generation system for idle game.
Adapted from backend/autofighter/mapgen.py without async dependencies.
"""

from __future__ import annotations

import random
from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class MapNode:
    """Represents a single room/node in the map."""
    room_id: int
    room_type: str
    floor: int
    index: int
    loop: int = 1
    pressure: int = 0
    encounter_bonus: int = 0
    tags: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data["tags"] = list(self.tags)
        return data

    @classmethod
    def from_dict(cls, data: dict) -> MapNode:
        """Create from dictionary."""
        raw_tags = data.get("tags", ())
        if isinstance(raw_tags, (list, tuple)):
            tags: tuple[str, ...] = tuple(str(tag) for tag in raw_tags if tag)
        elif isinstance(raw_tags, str) and raw_tags:
            tags = (raw_tags,)
        else:
            tags = ()
        
        return cls(
            room_id=data.get('room_id', 0),
            room_type=data.get('room_type', 'battle-weak'),
            floor=data.get('floor', 1),
            index=data.get('index', 0),
            loop=data.get('loop', 1),
            pressure=data.get('pressure', 0),
            encounter_bonus=int(data.get('encounter_bonus', 0) or 0),
            tags=tags,
        )


class MapGenerator:
    """Generates floor maps with various room types."""
    
    ROOMS_PER_FLOOR = 15  # Simplified from 100
    
    def __init__(
        self,
        seed: str | None = None,
        *,
        floor: int = 1,
        loop: int = 1,
        pressure: int = 0,
        configuration: dict[str, Any] | None = None,
    ) -> None:
        """Initialize map generator.
        
        Args:
            seed: Random seed for deterministic generation
            floor: Current floor number
            loop: Current loop/ascension level
            pressure: Difficulty pressure
            configuration: Optional configuration dict
        """
        self._rand = random.Random(seed)
        self.floor = floor
        self.loop = loop
        self.pressure = pressure
        self.configuration = dict(configuration or {})

    def generate_floor(self, boss_rush: bool = False) -> list[MapNode]:
        """Generate a full floor of rooms.
        
        Args:
            boss_rush: If True, generate only boss battles
            
        Returns:
            List of MapNode objects representing the floor
        """
        if boss_rush:
            return self._generate_boss_rush_floor()
        
        nodes: list[MapNode] = []
        
        # Start room
        nodes.append(
            MapNode(
                room_id=0,
                room_type="start",
                floor=self.floor,
                index=0,
                loop=self.loop,
                pressure=self.pressure,
            )
        )
        
        # Middle rooms
        middle_count = self.ROOMS_PER_FLOOR - 2
        room_types = self._generate_middle_rooms(middle_count)
        
        for idx, room_type in enumerate(room_types, start=1):
            tags: tuple[str, ...] = ()
            if room_type == "battle-prime":
                tags = ("prime",)
            elif room_type == "battle-elite":
                tags = ("elite",)
            
            nodes.append(
                MapNode(
                    room_id=idx,
                    room_type=room_type,
                    floor=self.floor,
                    index=idx,
                    loop=self.loop,
                    pressure=self.pressure,
                    tags=tags,
                )
            )
        
        # Boss room
        nodes.append(
            MapNode(
                room_id=self.ROOMS_PER_FLOOR - 1,
                room_type="battle-boss",
                floor=self.floor,
                index=self.ROOMS_PER_FLOOR - 1,
                loop=self.loop,
                pressure=self.pressure,
            )
        )
        
        return nodes

    def _generate_middle_rooms(self, count: int) -> list[str]:
        """Generate room types for middle section of floor.
        
        Args:
            count: Number of rooms to generate
            
        Returns:
            List of room type strings
        """
        room_types: list[str] = []
        
        # Add 1-2 shops
        shop_count = 1 if count > 5 else 0
        room_types.extend(["shop"] * shop_count)
        
        # Add 1 rest room every 3 floors
        if self.floor % 3 == 0 and count > 3:
            room_types.append("rest")
        
        # Fill remaining with battles
        remaining = count - len(room_types)
        
        # Distribution: 60% normal, 30% weak, 10% elite/prime
        normal_count = int(remaining * 0.6)
        weak_count = int(remaining * 0.3)
        elite_count = remaining - normal_count - weak_count
        
        room_types.extend(["battle-normal"] * normal_count)
        room_types.extend(["battle-weak"] * weak_count)
        
        # Alternate between elite and prime for variety
        for i in range(elite_count):
            if i % 2 == 0:
                room_types.append("battle-elite")
            else:
                room_types.append("battle-prime")
        
        # Shuffle to randomize order
        self._rand.shuffle(room_types)
        
        # Ensure shops appear in latter half
        shops = [rt for rt in room_types if rt == "shop"]
        if shops:
            non_shops = [rt for rt in room_types if rt != "shop"]
            midpoint = len(non_shops) // 2
            room_types = non_shops[:midpoint] + shops + non_shops[midpoint:]
        
        return room_types

    def _generate_boss_rush_floor(self) -> list[MapNode]:
        """Generate a floor with only boss battles."""
        nodes: list[MapNode] = []
        
        for index in range(self.ROOMS_PER_FLOOR):
            room_type = "start" if index == 0 else "battle-boss"
            nodes.append(
                MapNode(
                    room_id=index,
                    room_type=room_type,
                    floor=self.floor,
                    index=index,
                    loop=self.loop,
                    pressure=self.pressure,
                )
            )
        
        return nodes
