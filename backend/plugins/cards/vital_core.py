from dataclasses import dataclass
from dataclasses import field

from plugins.cards._base import CardBase


@dataclass
class VitalCore(CardBase):
    id: str = "vital_core"
    name: str = "Vital Core"
    stars: int = 1
    effects: dict[str, float] = field(
        default_factory=lambda: {"vitality": 0.03, "max_hp": 0.03}
    )
