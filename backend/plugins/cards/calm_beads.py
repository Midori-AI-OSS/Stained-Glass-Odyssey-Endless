from dataclasses import dataclass
from dataclasses import field

from plugins.cards._base import CardBase


@dataclass
class CalmBeads(CardBase):
    id: str = "calm_beads"
    name: str = "Calm Beads"
    stars: int = 1
    effects: dict[str, float] = field(
        default_factory=lambda: {"effect_resistance": 0.03}
    )
