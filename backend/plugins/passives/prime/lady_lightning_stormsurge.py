from dataclasses import dataclass
from typing import TYPE_CHECKING

from autofighter.stat_effect import StatEffect
from plugins.passives.normal.lady_lightning_stormsurge import LadyLightningStormsurge

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class LadyLightningStormsurgePrime(LadyLightningStormsurge):
    """[PRIME] Stormsurge with taller tempo ceilings and harsher shocks."""

    plugin_type = "passive"
    id = "lady_lightning_stormsurge_prime"
    name = "Prime Stormsurge"
    trigger = ["action_taken", "hit_landed"]
    max_stacks = 1
    stack_display = "spinner"

    async def on_action_taken(self, target: "Stats", **kwargs) -> None:
        entity_id = id(target)
        current = self._tempo_stacks.get(entity_id, 0)
        tempo = min(current + 1, 6)
        self._tempo_stacks[entity_id] = tempo

        tempo_effect = StatEffect(
            name=f"{self.id}_tempo",
            stat_modifiers={
                "spd": tempo * 4,
                "effect_hit_rate": tempo * 0.07,
            },
            duration=2,
            source=self.id,
        )
        target.add_effect(tempo_effect)

    async def on_hit_target(
        self,
        attacker: "Stats",
        target_hit: "Stats",
        damage: int | None = None,
    ) -> None:
        if target_hit is None:
            return

        attacker_id = id(attacker)
        tempo = self._tempo_stacks.get(attacker_id, 0)
        if tempo <= 0:
            return

        key = (attacker_id, id(target_hit))
        shock = min(self._shock_stacks.get(key, 0) + 1, 6)
        self._shock_stacks[key] = shock

        slow_amount = -3 * max(1, tempo)
        resistance_penalty = -0.04 * shock

        shock_effect = StatEffect(
            name=f"{self.id}_shock_{attacker_id}",
            stat_modifiers={
                "spd": slow_amount,
                "effect_resistance": resistance_penalty,
            },
            duration=2,
            source=self.id,
        )
        target_hit.add_effect(shock_effect)

        attack_bonus = int(attacker.atk * 0.05 * min(tempo, 4))
        overload_effect = StatEffect(
            name=f"{self.id}_overload",
            stat_modifiers={"atk": attack_bonus},
            duration=2,
            source=self.id,
        )
        attacker.add_effect(overload_effect)

        self._tempo_stacks[attacker_id] = max(0, tempo - 1)

    @classmethod
    def get_description(cls) -> str:
        return (
            "[PRIME] Builds up to 6 Stormsurge stacks for +4 SPD and +7% effect hit each. "
            "Hits shock foes harder, stripping 4% resistance per shock and slowing them more while leaving a two-turn overload buff."
        )

