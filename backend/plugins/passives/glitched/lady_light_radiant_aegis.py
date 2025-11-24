from dataclasses import dataclass
from typing import TYPE_CHECKING

from plugins.passives.normal.lady_light_radiant_aegis import LadyLightRadiantAegis

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class LadyLightRadiantAegisGlitched(LadyLightRadiantAegis):
    """[GLITCHED] Lady Light's Radiant Aegis - doubled HoT shields.

    This glitched variant doubles the shield amount from HoTs (100% of HoT amount
    instead of 50%), providing significantly stronger protection while maintaining
    the same cleansing and resistance mechanics.
    """
    plugin_type = "passive"
    id = "lady_light_radiant_aegis_glitched"
    name = "Glitched Radiant Aegis"
    trigger = "action_taken"
    max_stacks = 1
    stack_display = "spinner"

    async def on_hot_applied(self, target: "Stats", healed_ally: "Stats", hot_amount: int) -> None:
        """Enhance HoTs with DOUBLED shields (100% instead of 50%)."""
        from autofighter.stat_effect import StatEffect

        # DOUBLED shield (100% of HoT amount instead of 50%)
        shield_amount = hot_amount  # Doubled from int(hot_amount * 0.5)

        if shield_amount > 0:
            if not healed_ally.overheal_enabled:
                healed_ally.enable_overheal()
            healed_ally.shields += shield_amount

        # Grant +5% effect resistance for one turn (unchanged)
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
            "[GLITCHED] HoTs grant shields equal to 100% of the heal (doubled) and +5% effect resistance for one turn. "
            "Cleansing a DoT heals 5% of max HP and gives Lady Light +2% attack per cleanse."
        )
