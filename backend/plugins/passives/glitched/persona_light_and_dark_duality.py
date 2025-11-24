from dataclasses import dataclass

from plugins.passives.normal.persona_light_and_dark_duality import (
    PersonaLightAndDarkDuality,
)


@dataclass
class PersonaLightAndDarkDualityGlitched(PersonaLightAndDarkDuality):
    """[GLITCHED] Persona Light and Dark's Duality - doubled stance bonuses.

    This glitched variant doubles all bonuses from Light (healing/shields) and
    Dark (damage/DoTs) stances, creating extreme swings between support and offense.
    """
    plugin_type = "passive"
    id = "persona_light_and_dark_duality_glitched"
    name = "Glitched Light and Dark Duality"
    trigger = "turn_start"
    max_stacks = 1
    stack_display = "spinner"

    @classmethod
    def get_description(cls) -> str:
        return (
            "[GLITCHED] Alternates between Light (doubled healing/shields) and Dark (doubled damage/DoTs) stances. "
            "Each stance provides doubled bonuses to its element's mechanics. "
            "Switching costs are reduced when balance is maintained."
        )
