from dataclasses import dataclass
from typing import TYPE_CHECKING

from plugins.passives.normal.luna_lunar_reservoir import LunaLunarReservoir

if TYPE_CHECKING:
    pass


@dataclass
class LunaLunarReservoirBoss(LunaLunarReservoir):
    """Luna's Boss-tier Lunar Reservoir - enhanced charge system for boss encounters.

    Boss variant of Luna's passive with increased charge capacity and more aggressive
    action scaling. Maintains the core charge mechanic but with boss-appropriate power levels.
    """
    plugin_type = "passive"
    id = "luna_lunar_reservoir_boss"
    name = "Lunar Reservoir (Boss)"
    trigger = ["action_taken", "ultimate_used", "hit_landed"]
    max_stacks = 4000  # Doubled soft cap for bosses
    stack_display = "number"

    @classmethod
    def get_description(cls) -> str:
        return (
            "[BOSS] Gains 1 charge per action. "
            "Every 25 charge doubles actions per turn (capped after 4000 doublings). "
            "Stacks above 4000 grant +55% of Luna's base ATK, +1% of her base SPD, "
            "and +1% additional actions from the doubled cadence per 100 excess charge with no automatic drain."
        )

