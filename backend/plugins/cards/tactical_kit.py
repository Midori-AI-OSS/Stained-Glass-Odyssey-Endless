from dataclasses import dataclass
from dataclasses import field

from plugins.cards._base import CardBase


@dataclass
class TacticalKit(CardBase):
    id: str = "tactical_kit"
    name: str = "Tactical Kit"
    stars: int = 1
    effects: dict[str, float] = field(
        default_factory=lambda: {"atk": 0.02, "max_hp": 0.02}
    )
