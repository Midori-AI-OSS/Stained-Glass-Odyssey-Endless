from dataclasses import dataclass
from dataclasses import field

from plugins.cards._base import CardBase


@dataclass
class ReinforcedCloak(CardBase):
    id: str = "reinforced_cloak"
    name: str = "Reinforced Cloak"
    stars: int = 1
    effects: dict[str, float] = field(
        default_factory=lambda: {"defense": 0.03, "effect_resistance": 0.03}
    )
