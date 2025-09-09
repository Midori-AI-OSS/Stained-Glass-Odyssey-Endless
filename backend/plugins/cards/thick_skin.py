from dataclasses import dataclass
from dataclasses import field

from plugins.cards._base import CardBase


@dataclass
class ThickSkin(CardBase):
    id: str = "thick_skin"
    name: str = "Thick Skin"
    stars: int = 1
    effects: dict[str, float] = field(default_factory=lambda: {"bleed_resist": 0.03})
