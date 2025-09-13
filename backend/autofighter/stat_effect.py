from dataclasses import dataclass
from typing import Dict
from typing import Union


@dataclass
class StatEffect:
    """Represents a temporary effect that modifies stats."""
    name: str
    stat_modifiers: Dict[str, Union[int, float]]
    duration: int = -1  # -1 for permanent effects (cards/relics), >0 for temporary
    source: str = "unknown"  # source identifier (card name, relic name, etc.)

    def is_expired(self) -> bool:
        """Check if this effect has expired."""
        return self.duration == 0

    def tick(self) -> None:
        """Reduce duration by 1 if it's a temporary effect."""
        if self.duration > 0:
            self.duration -= 1
