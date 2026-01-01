from dataclasses import dataclass
from typing import TYPE_CHECKING

from plugins.passives.normal.luna_lunar_reservoir import LunaLunarReservoir

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class LunaLunarReservoirGlitched(LunaLunarReservoir):
    """Luna's Glitched Lunar Reservoir - charge system with doubled gains and instability.

    This glitched variant doubles charge gains and sword output, creating an unstable
    but more powerful version of Luna's base passive. The glitched modifier affects
    all charge sources: actions, ultimates, hits, and sword strikes.
    """
    plugin_type = "passive"
    id = "luna_lunar_reservoir_glitched"
    name = "Glitched Lunar Reservoir"
    trigger = ["action_taken", "ultimate_used", "hit_landed"]
    max_stacks = 2000
    stack_display = "number"

    @classmethod
    def _charge_multiplier(cls, _charge_holder: "Stats") -> int:
        """Glitched variant always has 2x charge multiplier."""
        return 2

    @classmethod
    def _sword_charge_amount(cls, owner: "Stats | None") -> int:
        """Glitched variant has doubled sword charge."""
        if owner is None:
            return 0
        return 2  # Base 1 * 2 for glitched

    @classmethod
    def get_description(cls) -> str:
        return (
            "[GLITCHED] Gains 2 charge per action (doubled). "
            "Every 25 charge doubles actions per turn (capped after 2000 doublings). "
            "Stacks above 2000 grant +55% of Luna's base ATK, +1% of her base SPD, "
            "and +1% additional actions from the doubled cadence per 100 excess charge with no automatic drain. "
            "Sword hits grant 2 charge (doubled)."
        )

