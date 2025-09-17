from dataclasses import dataclass
from dataclasses import field
import random

from autofighter.stats import BUS
from plugins.relics._base import RelicBase


@dataclass
class TimekeepersHourglass(RelicBase):
    """Each turn, 10% +1% per stack chance for allies to gain an extra turn."""

    id: str = "timekeepers_hourglass"
    name: str = "Timekeeper's Hourglass"
    stars: int = 4
    effects: dict[str, float] = field(default_factory=dict)
    about: str = "Each turn, 10% +1% per stack chance for allies to gain an extra turn."

    async def apply(self, party) -> None:
        if getattr(party, "_t_hourglass_applied", False):
            return
        party._t_hourglass_applied = True
        await super().apply(party)

        stacks = party.relics.count(self.id)
        chance = 0.10 + 0.01 * (stacks - 1)

        async def _turn_start() -> None:
            if random.random() < chance:
                for member in party.members:
                    await BUS.emit_async("extra_turn", member)

        def _battle_end(_entity) -> None:
            BUS.unsubscribe("turn_start", _turn_start)
            BUS.unsubscribe("battle_end", _battle_end)
            if hasattr(party, "_t_hourglass_applied"):
                delattr(party, "_t_hourglass_applied")

        BUS.subscribe("turn_start", _turn_start)
        BUS.subscribe("battle_end", _battle_end)

    def describe(self, stacks: int) -> str:
        pct = 10 + 1 * (stacks - 1)
        return f"Each turn, {pct}% chance for allies to gain an extra turn."