from dataclasses import dataclass
from typing import TYPE_CHECKING

from plugins.passives.normal.lady_darkness_eclipsing_veil import LadyDarknessEclipsingVeil

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class LadyDarknessEclipsingVeilBoss(LadyDarknessEclipsingVeil):
    """Boss DoT siphon that leeches 1.5% of all ticks."""

    plugin_type = "passive"
    id = "lady_darkness_eclipsing_veil_boss"
    name = "Eclipsing Veil (Boss)"
    trigger = "turn_start"
    max_stacks = 1
    stack_display = "spinner"

    async def on_dot_tick(self, target: "Stats", dot_damage: int) -> None:
        """Heal for 1.5% of any DoT applied to tracked combatants."""

        siphoned_healing = max(1, int(dot_damage * 0.015))
        await target.apply_healing(siphoned_healing)

    @classmethod
    def get_description(cls) -> str:
        return (
            "[BOSS] Extends DoTs by 1 turn and siphons 1.5% of each tick as healing while keeping the debuff-resist attack stacks from the base passive."
        )
