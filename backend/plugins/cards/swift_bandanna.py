from dataclasses import dataclass
from dataclasses import field

from plugins.cards._base import CardBase


@dataclass
class SwiftBandanna(CardBase):
    id: str = "swift_bandanna"
    name: str = "Swift Bandanna"
    stars: int = 1
    effects: dict[str, float] = field(
        default_factory=lambda: {"crit_rate": 0.03, "dodge_odds": 0.03}
    )
