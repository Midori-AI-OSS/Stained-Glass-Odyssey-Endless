"""Stat effect system for temporary and permanent stat modifications.

This module provides the StatEffect class for managing temporary buffs, debuffs,
and permanent stat modifications from cards, relics, and other sources.
"""

from dataclasses import dataclass
from typing import Dict
from typing import Union


@dataclass
class StatEffect:
    """Represents a temporary or permanent effect that modifies stats.

    Effects can modify any stat by name (e.g., 'atk', 'defense', 'crit_rate').
    Effects with duration > 0 are temporary and expire after ticking down.
    Effects with duration = -1 are permanent (from cards/relics).

    Attributes:
        name: Unique identifier for this effect (e.g., 'attack_up', 'shield_buff')
        stat_modifiers: Dictionary mapping stat names to modifier values
        duration: Turns remaining (-1 for permanent, 0 for expired, >0 for temporary)
        source: Source identifier (card name, relic name, ability name, etc.)
    """

    name: str
    stat_modifiers: Dict[str, Union[int, float]]
    duration: int = -1  # -1 for permanent effects, >0 for temporary
    source: str = "unknown"

    def is_expired(self) -> bool:
        """Check if this effect has expired.

        Returns:
            True if duration is exactly 0, False otherwise
        """
        return self.duration == 0

    def tick(self) -> None:
        """Reduce duration by 1 turn if this is a temporary effect.

        Permanent effects (duration = -1) are not affected.
        Expired effects (duration = 0) remain at 0.
        """
        if self.duration > 0:
            self.duration -= 1
