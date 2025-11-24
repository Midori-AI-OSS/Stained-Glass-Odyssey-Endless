from dataclasses import dataclass
from typing import TYPE_CHECKING

from autofighter.stat_effect import StatEffect
from plugins.passives.normal.mezzy_gluttonous_bulwark import MezzyGluttonousBulwark

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class MezzyGluttonousBulwarkPrime(MezzyGluttonousBulwark):
    """[PRIME] Gluttonous Bulwark with deeper siphons and regen."""

    plugin_type = "passive"
    id = "mezzy_gluttonous_bulwark_prime"
    name = "Prime Gluttonous Bulwark"
    trigger = "turn_start"
    max_stacks = 1
    stack_display = "spinner"

    async def apply(self, target: "Stats", allies: list["Stats"] | None = None, **kwargs: object) -> None:
        await super().apply(target, allies=allies, **kwargs)

        regen = StatEffect(
            name=f"{self.id}_regen",
            stat_modifiers={"regain": max(5, int(target.max_hp * 0.02))},
            duration=-1,
            source=self.id,
        )
        target.add_effect(regen)

    async def siphon_from_allies(self, mezzy: "Stats", allies: list["Stats"]) -> None:
        await super().siphon_from_allies(mezzy, allies)

        mezzy_id = id(mezzy)
        for ally in allies:
            ally_id = id(ally)
            if ally_id == mezzy_id or ally.hp <= 0:
                continue
            siphon = StatEffect(
                name=f"{self.id}_siphon_bonus_{ally_id}",
                stat_modifiers={"atk": max(1, int(getattr(ally, "atk", 0) * 0.02))},
                duration=1,
                source=self.id,
            )
            mezzy.add_effect(siphon)

    @classmethod
    def get_description(cls) -> str:
        return (
            "[PRIME] Keeps the 20% damage reduction but adds steady regen. Siphons hit twice as hard, granting bonus attack taps each turn from healthy allies while returning more when they fall low."
        )

