from dataclasses import dataclass
from dataclasses import field

from plugins.cards._base import CardBase


@dataclass
class BulwarkTotem(CardBase):
    id: str = "bulwark_totem"
    name: str = "Bulwark Totem"
    stars: int = 1
    effects: dict[str, float] = field(
        default_factory=lambda: {"defense": 0.02, "max_hp": 0.02}
    )
