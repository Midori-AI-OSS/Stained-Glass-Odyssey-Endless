from dataclasses import dataclass

from plugins.passives.normal.lady_of_fire_infernal_momentum import (
    LadyOfFireInfernalMomentum,
)


@dataclass
class LadyOfFireInfernalMomentumGlitched(LadyOfFireInfernalMomentum):
    """[GLITCHED] Lady of Fire's Infernal Momentum - doubled missing HP bonus.

    This glitched variant doubles the fire damage bonus from missing HP,
    making low-health burns and counters significantly more devastating.
    """
    plugin_type = "passive"
    id = "lady_of_fire_infernal_momentum_glitched"
    name = "Glitched Infernal Momentum"
    trigger = "damage_taken"
    max_stacks = 1
    stack_display = "spinner"

    @classmethod
    def get_description(cls) -> str:
        return (
            "[GLITCHED] Doubles Fire's missing HP damage bonus (120% instead of 60%). "
            "When taking damage, applies burn DoT to attacker. "
            "Self-damage heals allies and grants temporary damage boost."
        )
