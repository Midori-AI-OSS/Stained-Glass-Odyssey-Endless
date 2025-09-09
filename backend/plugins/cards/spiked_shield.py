from dataclasses import dataclass
from dataclasses import field

from plugins.cards._base import CardBase


@dataclass
class SpikedShield(CardBase):
    id: str = "spiked_shield"
    name: str = "Spiked Shield"
    stars: int = 1
    effects: dict[str, float] = field(
        default_factory=lambda: {"atk": 0.03, "defense": 0.03}
    )
