from dataclasses import dataclass

from plugins.passives.normal.persona_ice_cryo_cycle import PersonaIceCryoCycle


@dataclass
class PersonaIceCryoCycleGlitched(PersonaIceCryoCycle):
    """[GLITCHED] Persona Ice's Cryo Cycle - doubled freeze duration and chill stacks.

    This glitched variant doubles the effectiveness of freeze mechanics and
    chill stacking, making Ice Persona an even more dominant crowd controller.
    """
    plugin_type = "passive"
    id = "persona_ice_cryo_cycle_glitched"
    name = "Glitched Cryo Cycle"
    trigger = "hit_landed"
    max_stacks = 1
    stack_display = "spinner"

    @classmethod
    def get_description(cls) -> str:
        return (
            "[GLITCHED] Ice attacks apply chill stacks (doubled). "
            "High chill causes freeze (doubled duration). "
            "Frozen enemies take doubled damage from Ice attacks."
        )
