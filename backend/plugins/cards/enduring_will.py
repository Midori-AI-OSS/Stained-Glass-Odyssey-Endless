from dataclasses import dataclass
from dataclasses import field

from plugins.cards._base import CardBase


@dataclass
class EnduringWill(CardBase):
    id: str = "enduring_will"
    name: str = "Enduring Will"
    stars: int = 1
    effects: dict[str, float] = field(
        default_factory=lambda: {"mitigation": 0.03, "vitality": 0.03}
    )
