from dataclasses import dataclass
from typing import TYPE_CHECKING

from autofighter.stat_effect import StatEffect
from plugins.passives.normal.lady_lightning_stormsurge import LadyLightningStormsurge

if TYPE_CHECKING:
    from autofighter.stats import Stats


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
    trigger = ["action_taken", "hit_landed"]
    max_stacks = 1
    stack_display = "spinner"

    async def on_action_taken(self, target: "Stats", **kwargs) -> None:
        """Build tempo stacks with DOUBLED bonuses."""

        entity_id = id(target)
        current = self._tempo_stacks.get(entity_id, 0)
        tempo = min(current + 1, 4)
        self._tempo_stacks[entity_id] = tempo

        # DOUBLED: +6 SPD and +10% effect hit rate per stack (was +3 and +5%)
        tempo_effect = StatEffect(
            name=f"{self.id}_tempo",
            stat_modifiers={
                "spd": tempo * 6,  # Was tempo * 3
                "effect_hit_rate": tempo * 0.10,  # Was tempo * 0.05
            },
            duration=2,
            source=self.id,
        )
        target.add_effect(tempo_effect)

    @classmethod
    def get_description(cls) -> str:
        return (
            "[GLITCHED] Build tempo stacks on action (max 4) granting +6 SPD and +10% effect hit (doubled per stack). "
            "DoT ticks inflict shock stacks on enemies. Multiple shock stacks trigger chain reactions."
        )
