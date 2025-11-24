from dataclasses import dataclass

from plugins.passives.normal.lady_echo_resonant_static import LadyEchoResonantStatic


@dataclass
class LadyEchoResonantStaticGlitched(LadyEchoResonantStatic):
    """[GLITCHED] Lady Echo's Resonant Static - doubled consecutive hit bonuses.

    This glitched variant doubles all damage and effect bonuses from consecutive
    hits, making the chain lightning mechanic significantly more powerful when
    focusing on a single target.
    """
    plugin_type = "passive"
    id = "lady_echo_resonant_static_glitched"
    name = "Glitched Resonant Static"
    trigger = "hit_landed"
    max_stacks = 1
    stack_display = "spinner"

    @classmethod
    def get_description(cls) -> str:
        return (
            "[GLITCHED] Chain damage scales with DoTs on target. "
            "Consecutive hits on same target double damage and crit rate (doubled bonuses). "
            "Switching targets grants party-wide crit rate based on hit streak."
        )
