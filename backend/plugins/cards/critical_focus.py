from dataclasses import dataclass
from dataclasses import field

from autofighter.stats import BUS
from plugins.cards._base import CardBase
from plugins.effects.critical_boost import CriticalBoost


@dataclass
class CriticalFocus(CardBase):
    id: str = "critical_focus"
    name: str = "Critical Focus"
    stars: int = 2
    effects: dict[str, float] = field(default_factory=lambda: {"atk": 0.55})
    about: str = "+55% ATK; allies gain Critical Boost each turn."

    async def apply(self, party) -> None:  # type: ignore[override]
        await super().apply(party)
        boosts: dict[int, CriticalBoost] = {}

        async def _turn_start() -> None:
            for member in party.members:
                pid = id(member)
                effect = boosts.get(pid)
                if effect is None:
                    effect = CriticalBoost()
                    boosts[pid] = effect
                    setattr(member, "_critical_boost", effect)
                await effect.apply(member)
                await BUS.emit_async(
                    "card_effect",
                    self.id,
                    member,
                    "critical_boost_stack",
                    effect.stacks,
                    {"stacks": effect.stacks},
                )

        self.subscribe("turn_start", _turn_start)
