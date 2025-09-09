from dataclasses import dataclass
from dataclasses import field

from plugins.cards._base import CardBase


@dataclass
class SteadyGrip(CardBase):
    id: str = "steady_grip"
    name: str = "Steady Grip"
    stars: int = 1
    effects: dict[str, float] = field(
        default_factory=lambda: {"atk": 0.03, "dodge_odds": 0.03}
    )
