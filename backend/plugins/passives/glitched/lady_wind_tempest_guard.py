from dataclasses import dataclass

from plugins.passives.normal.lady_wind_tempest_guard import LadyWindTempestGuard


@dataclass
class LadyWindTempestGuardGlitched(LadyWindTempestGuard):
    """[GLITCHED] Lady Wind's Tempest Guard - doubled gust stack bonuses.

    This glitched variant doubles the defensive bonuses from gust stacks
    (dodge, damage reduction, speed), making the defensive stance much stronger
    while critical hits still consume stacks for powerful counters.
    """
    plugin_type = "passive"
    id = "lady_wind_tempest_guard_glitched"
    name = "Glitched Tempest Guard"
    trigger = "turn_start"
    max_stacks = 5
    stack_display = "pips"

    @classmethod
    def get_description(cls) -> str:
        return (
            "[GLITCHED] Build gust stacks at turn start (max 5) providing doubled dodge, damage reduction, and speed. "
            "Scoring a critical hit consumes one gust to trigger Wind Slash (area damage). "
            "Higher gust count makes Wind Slash more powerful."
        )
