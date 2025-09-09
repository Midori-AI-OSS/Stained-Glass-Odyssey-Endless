from dataclasses import dataclass
from dataclasses import field

from plugins.cards._base import CardBase


@dataclass
class BalancedDiet(CardBase):
    id: str = "balanced_diet"
    name: str = "Balanced Diet"
    stars: int = 1
    effects: dict[str, float] = field(
        default_factory=lambda: {"max_hp": 0.03, "defense": 0.03}
    )
