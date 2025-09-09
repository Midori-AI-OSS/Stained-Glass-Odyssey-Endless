from dataclasses import dataclass
from dataclasses import field

from plugins.relics._base import RelicBase


@dataclass
class FallbackEssence(RelicBase):
    """A fallback relic granted when the card pool is exhausted. Provides a small boost to all stats."""

    id: str = "fallback_essence"
    name: str = "Essence of 6858"
    stars: int = 6
    effects: dict[str, float] = field(
        default_factory=lambda: {
            "atk": 0.01,
            "defense": 0.01,
            "max_hp": 0.01,
            "crit_rate": 0.01,
            "crit_damage": 0.01,
            "effect_hit_rate": 0.01,
            "effect_resistance": 0.01,
        }
    )
    about: str = (
        "A mystical essence that forms when one's determination transcends the need for material cards. "
        "+1% to core combat stats."
    )

    def describe(self, stacks: int) -> str:
        if stacks == 1:
            return "When the card pool is exhausted, grants +1% to core combat stats."
        else:
            # Calculate actual multiplicative bonus: (1.01)^stacks - 1
            multiplier = (1.01**stacks) - 1
            total_pct = round(multiplier * 100)
            return f"When the card pool is exhausted, grants +{total_pct}% to core combat stats ({stacks} stacks, multiplicative)."
