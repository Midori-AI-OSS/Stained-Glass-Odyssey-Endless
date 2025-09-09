from dataclasses import dataclass
from dataclasses import field

from plugins.cards._base import CardBase


@dataclass
class CoatedArmor(CardBase):
    id: str = "coated_armor"
    name: str = "Coated Armor"
    stars: int = 1
    effects: dict[str, float] = field(
        default_factory=lambda: {"mitigation": 0.03, "defense": 0.03}
    )
