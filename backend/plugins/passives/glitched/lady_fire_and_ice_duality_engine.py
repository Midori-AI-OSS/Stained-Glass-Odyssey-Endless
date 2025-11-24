from dataclasses import dataclass

from plugins.passives.normal.lady_fire_and_ice_duality_engine import (
    LadyFireAndIceDualityEngine,
)


@dataclass
class LadyFireAndIceDualityEngineGlitched(LadyFireAndIceDualityEngine):
    """[GLITCHED] Lady Fire and Ice's Duality Engine - doubled flux stacks.

    This glitched variant doubles the benefit from Elemental Flux stacks when
    alternating between fire and ice elements, providing much stronger party
    buffs and enemy debuffs.
    """
    plugin_type = "passive"
    id = "lady_fire_and_ice_duality_engine_glitched"
    name = "Glitched Duality Engine"
    trigger = "action_taken"
    max_stacks = 1
    stack_display = "spinner"

    @classmethod
    def get_description(cls) -> str:
        return (
            "[GLITCHED] Alternating between Fire and Ice builds Elemental Flux stacks (doubled benefits). "
            "Fire applies DoTs, Ice provides defensive bonuses. "
            "High flux stacks enhance both elements significantly."
        )
