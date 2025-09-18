import asyncio
from dataclasses import dataclass
from dataclasses import field

from autofighter.stats import BUS
from autofighter.stats import Stats
from plugins.cards._base import CardBase
from plugins.cards._base import safe_async_task


@dataclass
class Overclock(CardBase):
    """+500% ATK & Effect Hit Rate; allies act twice at battle start."""

    id: str = "overclock"
    name: str = "Overclock"
    stars: int = 4
    effects: dict[str, float] = field(
        default_factory=lambda: {"atk": 5, "effect_hit_rate": 5}
    )
    about: str = (
        "+500% ATK & +500% Effect Hit Rate; at the start of each battle, "
        "all allies immediately take two actions back to back."
    )

    async def apply(self, party) -> None:  # type: ignore[override]
        await super().apply(party)

        async def _double_act(ally: Stats) -> None:
            for _ in range(2):
                await BUS.emit_async("extra_turn", ally)
                await BUS.emit_async(
                    "card_effect",
                    self.id,
                    ally,
                    "extra_action",
                    0,
                    {},
                )
                await asyncio.sleep(0.002)

        def _battle_start(entity: Stats) -> None:
            if entity in party.members:
                safe_async_task(_double_act(entity))

        BUS.subscribe("battle_start", _battle_start)