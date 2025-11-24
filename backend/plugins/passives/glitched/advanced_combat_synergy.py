from dataclasses import dataclass

from plugins.passives.normal.advanced_combat_synergy import AdvancedCombatSynergy


@dataclass
class AdvancedCombatSynergyGlitched(AdvancedCombatSynergy):
    """[GLITCHED] Advanced Combat Synergy - doubled party-wide bonuses.

    This glitched variant doubles all party-wide stat bonuses from coordination,
    making party synergy effects much more impactful.
    """
    plugin_type = "passive"
    id = "advanced_combat_synergy_glitched"
    name = "Glitched Combat Synergy"
    trigger = "turn_start"
    max_stacks = 1
    stack_display = "spinner"

    @classmethod
    def get_description(cls) -> str:
        return (
            "[GLITCHED] Grants party-wide bonuses based on party composition (doubled). "
            "More diverse damage types provide stronger synergy effects. "
            "Coordinated attacks trigger combo bonuses."
        )
