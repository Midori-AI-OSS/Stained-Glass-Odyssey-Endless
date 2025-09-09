from dataclasses import dataclass
from dataclasses import field

from plugins.cards._base import CardBase


@dataclass
class EnergizingTea(CardBase):
    id: str = "energizing_tea"
    name: str = "Energizing Tea"
    stars: int = 1
    effects: dict[str, float] = field(default_factory=lambda: {"regain": 0.03})
