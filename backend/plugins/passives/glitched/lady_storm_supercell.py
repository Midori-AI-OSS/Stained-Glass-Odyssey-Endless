from dataclasses import dataclass

from plugins.passives.normal.lady_storm_supercell import LadyStormSupercell


@dataclass
class LadyStormSupercellGlitched(LadyStormSupercell):
    """[GLITCHED] Lady Storm's Supercell - doubled Wind/Lightning enhancements.

    This glitched variant doubles all stat bonuses from Wind and Lightning phases,
    creating an extremely powerful dual-element stance system.
    """
    plugin_type = "passive"
    id = "lady_storm_supercell_glitched"
    name = "Glitched Supercell"
    trigger = "turn_start"
    max_stacks = 1
    stack_display = "spinner"

    @classmethod
    def get_description(cls) -> str:
        return (
            "[GLITCHED] Persistent Wind enhancements (doubled SPD/dodge) with Lightning charge buildup. "
            "Alternates between Wind (evasion) and Lightning (offense) phases automatically, "
            "providing massive stat swings based on current phase."
        )
