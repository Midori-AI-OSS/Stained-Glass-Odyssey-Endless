from dataclasses import dataclass
from dataclasses import field

from plugins.cards._base import CardBase


@dataclass
class GuidingCompass(CardBase):
    id: str = "guiding_compass"
    name: str = "Guiding Compass"
    stars: int = 1
    effects: dict[str, float] = field(
        default_factory=lambda: {"exp_multiplier": 0.03, "effect_hit_rate": 0.03}
    )
