from dataclasses import dataclass

from plugins.passives.normal.lady_lightning_stormsurge import LadyLightningStormsurge


@dataclass
class LadyLightningStormsurgeGlitched(LadyLightningStormsurge):
    """[GLITCHED] Lady Lightning's Stormsurge - doubled tempo bonuses.

    This glitched variant doubles the speed and effect hit rate bonuses from
    tempo stacks, making the ramp-up much more powerful and allowing for
    overwhelming DoT application.
    """
    plugin_type = "passive"
    id = "lady_lightning_stormsurge_glitched"
    name = "Glitched Stormsurge"
    trigger = "action_taken"
    max_stacks = 4
    stack_display = "number"

    @classmethod
    def get_description(cls) -> str:
        return (
            "[GLITCHED] Build tempo stacks on action (max 4) granting +6 SPD and +10% effect hit (doubled per stack). "
            "DoT ticks inflict shock stacks on enemies. Multiple shock stacks trigger chain reactions."
        )
