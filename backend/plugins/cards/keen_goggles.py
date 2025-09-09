from dataclasses import dataclass
from dataclasses import field

from plugins.cards._base import CardBase


@dataclass
class KeenGoggles(CardBase):
    id: str = "keen_goggles"
    name: str = "Keen Goggles"
    stars: int = 1
    effects: dict[str, float] = field(
        default_factory=lambda: {"crit_rate": 0.03, "effect_hit_rate": 0.03}
    )
