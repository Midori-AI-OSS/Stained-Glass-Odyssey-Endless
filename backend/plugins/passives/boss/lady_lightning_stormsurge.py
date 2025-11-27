from dataclasses import dataclass
from typing import TYPE_CHECKING

from autofighter.stat_effect import StatEffect
from plugins.passives.normal.lady_lightning_stormsurge import LadyLightningStormsurge

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class LadyLightningStormsurgeBoss(LadyLightningStormsurge):
    """Boss Stormsurge with 1.5× tempo bonuses per stack."""

    plugin_type = "passive"
    id = "lady_lightning_stormsurge_boss"
    name = "Stormsurge (Boss)"
    trigger = ["action_taken", "hit_landed"]
    max_stacks = 1
    stack_display = "spinner"

    async def on_action_taken(self, target: "Stats", **kwargs) -> None:
        entity_id = id(target)
        current = self._tempo_stacks.get(entity_id, 0)
        tempo = min(current + 1, 4)
        self._tempo_stacks[entity_id] = tempo

        spd_bonus = int(tempo * 4.5)
        effect_hit_bonus = tempo * 0.075

        tempo_effect = StatEffect(
            name=f"{self.id}_tempo",
            stat_modifiers={
                "spd": spd_bonus,
                "effect_hit_rate": effect_hit_bonus,
            },
            duration=2,
            source=self.id,
        )
        target.add_effect(tempo_effect)

    @classmethod
    def get_description(cls) -> str:
        return (
            "[BOSS] Tempo stacks grant +4.5 SPD and +7.5% effect hit per stack (max 4) while retaining the shock detonation package from the base passive."
        )
