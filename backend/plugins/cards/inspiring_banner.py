from dataclasses import dataclass
from dataclasses import field

from plugins.cards._base import CardBase


@dataclass
class InspiringBanner(CardBase):
    id: str = "inspiring_banner"
    name: str = "Inspiring Banner"
    stars: int = 1
    effects: dict[str, float] = field(
        default_factory=lambda: {"atk": 0.02, "defense": 0.02}
    )
