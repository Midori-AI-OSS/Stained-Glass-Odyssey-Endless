from dataclasses import dataclass
from dataclasses import field

from plugins.cards._base import CardBase


@dataclass
class BattleMeditation(CardBase):
    id: str = "battle_meditation"
    name: str = "Battle Meditation"
    stars: int = 1
    effects: dict[str, float] = field(
        default_factory=lambda: {"exp_multiplier": 0.03, "vitality": 0.03}
    )
