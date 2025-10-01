from dataclasses import dataclass
from dataclasses import field
import random

from autofighter.stats import BUS
from plugins.cards._base import CardBase
from plugins.cards._base import safe_async_task


@dataclass
class ArcaneRepeater(CardBase):
    """+500% ATK; 30% chance for attacks to repeat at 50% power."""

    id: str = "arcane_repeater"
    name: str = "Arcane Repeater"
    stars: int = 4
    effects: dict[str, float] = field(default_factory=lambda: {"atk": 5})
    about: str = (
        "+500% ATK; each attack has a 30% chance to immediately repeat at 50% power."
    )

    async def apply(self, party) -> None:  # type: ignore[override]
        await super().apply(party)

        async def _hit_landed(
            attacker,
            target,
            amount,
            source_type: str | None = "attack",
            source_name: str | None = None,
            *_args,
        ) -> None:
            if attacker not in party.members:
                return
            if source_type != "attack":
                return
            if target is None:
                return
            if amount is None:
                return
            if random.random() >= 0.30:
                return
            dmg = int(amount * 0.5)
            await BUS.emit_async(
                "card_effect",
                self.id,
                attacker,
                "repeat_attack",
                dmg,
                {
                    "target": getattr(target, "id", str(target)),
                    "damage": dmg,
                    "original": amount,
                },
            )
            safe_async_task(target.apply_damage(dmg, attacker=attacker))

        self.subscribe("hit_landed", _hit_landed)
