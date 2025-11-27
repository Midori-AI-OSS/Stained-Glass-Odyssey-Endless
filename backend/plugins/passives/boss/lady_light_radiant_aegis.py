from dataclasses import dataclass
from typing import TYPE_CHECKING

from plugins.passives.normal.lady_light_radiant_aegis import LadyLightRadiantAegis

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class LadyLightRadiantAegisBoss(LadyLightRadiantAegis):
    """Boss Radiant Aegis that converts 75% of HoTs into shielding."""

    plugin_type = "passive"
    id = "lady_light_radiant_aegis_boss"
    name = "Radiant Aegis (Boss)"
    trigger = "action_taken"
    max_stacks = 1
    stack_display = "spinner"

    async def on_hot_applied(self, target: "Stats", healed_ally: "Stats", hot_amount: int) -> None:
        from autofighter.stat_effect import StatEffect

        shield_amount = max(1, int(hot_amount * 0.75))
        if shield_amount > 0:
            if not healed_ally.overheal_enabled:
                healed_ally.enable_overheal()
            healed_ally.shields += shield_amount

        resistance_effect = StatEffect(
            name=f"{self.id}_hot_resistance",
            stat_modifiers={"effect_resistance": 0.05},
            duration=1,
            source=self.id,
        )
        healed_ally.add_effect(resistance_effect)

    @classmethod
    def get_description(cls) -> str:
        return (
            "[BOSS] HoTs grant shields equal to 75% of the heal (vs. 50% baseline) and still provide +5% effect resistance for one turn."
        )
