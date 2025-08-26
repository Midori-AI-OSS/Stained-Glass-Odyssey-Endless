
from typing import Any, Dict, Optional

import pygame

from damagetypes import DamageType
from damagetypes import Generic
from load_photos import set_themed_dot_photo
from plugins.dots.base import DotPlugin
from plugins.plugin_loader import PluginLoader

class dot:
    """
    Represents a Damage Over Time (DOT) effect applied to a character or entity.

    Attributes:
        name (str): The name of the DOT effect (e.g., "Poison," "Burn").
        damage (float): The amount of damage dealt per turn by the DOT.
        turns (int): The number of turns the DOT effect lasts.  Must be greater than 0.
        damage_type (DamageType):  The type of damage the DOT inflicts (e.g., "fire", "poison", "bleed").
        source (Optional[str]):  Optional name or identifier of the entity that applied the DOT.  Helps track responsibility.
        metadata (Optional[Dict[str, Any]]):  Optional dictionary for storing extra information, like the spell or ability that caused the DOT.
        tick_interval (int): how many times to do the effect each turn, good if you want to do it fast and for less time.

    Raises:
        ValueError: If 'turns' is not a integer.
    """
    def __init__(self, name: str, damage: float, turns: int, damage_type: DamageType = Generic, source: Optional[str] = None, tick_interval: int = 1, metadata: Optional[Dict[str, Any]] = None) -> None:
        if not isinstance(turns, int):
            raise ValueError("Turns must be a integer.")

        self.name: str = name
        self.damage: float = damage
        self.turns: int = turns
        self.max_turns: int = 5000
        self.damage_type: DamageType = damage_type
        self.source: Optional[str] = source
        self.metadata: Optional[Dict[str, Any]] = metadata
        self.tick_interval: int = tick_interval
        self.photodata = pygame.image.load(self.set_photo())

    def set_photo(self):
        return set_themed_dot_photo(self.damage_type.name.lower())

    def __repr__(self) -> str:
        return f"DOT(name='{self.name}', damage={self.damage}, turns={self.turns}, type={self.damage_type.name})"
    
    def check_turns(self) -> None:
        """
        Checks the turns remaining, if over a set number, grants more ticks per turn
        """
        if self.turns > self.max_turns:
            self.turns = round(self.turns / 2)
            self.tick_interval += 1

    def tick(self) -> float:
        """
        Reduces the remaining duration of the DOT.

        Returns:
            The damage dealt this tick.  Returns 0 if the DOT has expired.
        """
        
        self.check_turns()

        if self.turns > 0:
            self.turns -= 1
            return self.damage
        
        return 0

    def is_active(self) -> bool:
        """
        Checks if the DOT is still active (has remaining turns).

        Returns:
            True if the DOT is active, False otherwise.
        """
        return self.turns > 0


def get_dot(
    dot_id: str,
    *,
    plugin_dir: str = "plugins",
    **kwargs: Any,
) -> DotPlugin | dot:
    """Return a DOT plugin instance or fallback ``dot``."""

    loader = PluginLoader()
    loader.discover(plugin_dir)
    dot_cls = loader.get_plugins("dot").get(dot_id)
    if dot_cls is not None:
        return dot_cls(**kwargs)
    return dot(**kwargs)
