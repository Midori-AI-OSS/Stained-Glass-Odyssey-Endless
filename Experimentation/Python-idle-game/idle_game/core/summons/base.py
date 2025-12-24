"""
Base summon class for idle game.
Simplified from backend/autofighter/summons/base.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
import random
from typing import Any

from ..stats import Stats


@dataclass
class Summon(Stats):
    """Represents a summoned entity with proper stat inheritance.
    
    Summons inherit stats from their summoner and have limited lifetimes.
    They act in combat like regular characters but may disappear after
    a certain number of turns or when defeated.
    """

    # Summon-specific properties
    instance_id: str = ""
    summoner_id: str = ""
    summon_type: str = "generic"
    summon_source: str = "unknown"  # card/passive/relic that created this
    is_temporary: bool = True
    turns_remaining: int = -1  # -1 for permanent, >0 for temporary

    # Summon AI behavior
    ai_behavior: str = field(default="aggressive", init=False)
    target_priority: str = field(default="random", init=False)

    def __post_init__(self):
        """Initialize summon with proper inheritance from summoner."""
        super().__post_init__()

        # Mark this as a summon for identification
        if not self.instance_id:
            self.instance_id = f"{self.summoner_id}_{self.summon_type}_{random.randint(1000, 9999)}"

    @classmethod
    def create_from_summoner(
        cls,
        summoner: Stats,
        summon_type: str = "generic",
        source: str = "unknown",
        stat_multiplier: float = 0.5,
        turns_remaining: int = -1,
    ) -> Summon:
        """Create a summon based on a summoner's stats.
        
        Args:
            summoner: The entity summoning this
            summon_type: Type identifier for the summon
            source: Source that created this summon (card/passive/relic name)
            stat_multiplier: Multiplier for inherited stats (default 0.5 = 50%)
            turns_remaining: How many turns this summon lasts (-1 = permanent)
            
        Returns:
            New Summon instance
        """
        # Calculate base stats at specified multiplier
        base_hp = int(summoner.max_hp * stat_multiplier)
        base_atk = int(summoner.atk * stat_multiplier)
        base_def = int(summoner.defense * stat_multiplier)

        # Create the summon instance
        summon = cls(
            hp=base_hp,
            damage_type=summoner.damage_type,
            summoner_id=getattr(summoner, 'id', str(id(summoner))),
            summon_type=summon_type,
            summon_source=source,
            turns_remaining=turns_remaining,
            is_temporary=turns_remaining != -1,
        )

        # Set base stats after creation (they have init=False)
        summon._base_max_hp = base_hp
        summon._base_atk = base_atk
        summon._base_defense = base_def

        return summon

    def tick_turn(self) -> bool:
        """Decrement turn counter if temporary.
        
        Returns:
            True if summon should remain, False if it should despawn
        """
        if not self.is_temporary or self.turns_remaining < 0:
            return True

        self.turns_remaining -= 1

        return self.turns_remaining > 0

    def is_alive(self) -> bool:
        """Check if summon is still alive."""
        return self.hp > 0

    def should_despawn(self) -> bool:
        """Check if summon should be removed from combat."""
        if not self.is_alive():
            return True

        if self.is_temporary and self.turns_remaining <= 0:
            return True

        return False

    def to_dict(self) -> dict[str, Any]:
        """Convert summon to dictionary for serialization.
        
        Returns:
            Dictionary representation
        """
        return {
            "instance_id": self.instance_id,
            "summoner_id": self.summoner_id,
            "summon_type": self.summon_type,
            "summon_source": self.summon_source,
            "is_temporary": self.is_temporary,
            "turns_remaining": self.turns_remaining,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "atk": self.atk,
            "defense": self.defense,
            "damage_type": self.damage_type,
            "ai_behavior": self.ai_behavior,
            "target_priority": self.target_priority,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Summon:
        """Create summon from dictionary.
        
        Args:
            data: Dictionary with summon data
            
        Returns:
            Summon instance
        """
        summon = cls(
            hp=data.get("hp", 100),
            damage_type=data.get("damage_type", "Generic"),
            instance_id=data.get("instance_id", ""),
            summoner_id=data.get("summoner_id", ""),
            summon_type=data.get("summon_type", "generic"),
            summon_source=data.get("summon_source", "unknown"),
            is_temporary=data.get("is_temporary", True),
            turns_remaining=data.get("turns_remaining", -1),
        )

        # Set base stats after creation (they have init=False)
        summon._base_max_hp = data.get("max_hp", 100)
        summon._base_atk = data.get("atk", 10)
        summon._base_defense = data.get("defense", 10)
        summon.ai_behavior = data.get("ai_behavior", "aggressive")
        summon.target_priority = data.get("target_priority", "random")

        return summon
