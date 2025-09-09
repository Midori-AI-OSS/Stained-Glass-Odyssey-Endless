from dataclasses import dataclass
from dataclasses import field

from plugins.cards._base import CardBase


@dataclass
class SturdyBoots(CardBase):
    id: str = "sturdy_boots"
    name: str = "Sturdy Boots"
    stars: int = 1
    effects: dict[str, float] = field(
        default_factory=lambda: {"dodge_odds": 0.03, "defense": 0.03}
    )
