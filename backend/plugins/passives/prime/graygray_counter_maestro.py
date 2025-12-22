from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import Optional

from autofighter.stat_effect import StatEffect
from plugins.passives.normal.graygray_counter_maestro import GraygrayCounterMaestro

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class GraygrayCounterMaestroPrime(GraygrayCounterMaestro):
    """[PRIME] Counter Maestro with faster bursts and tougher ripostes."""

    plugin_type = "passive"
    id = "graygray_counter_maestro_prime"
    name = "Prime Counter Maestro"
    trigger = "damage_taken"
    max_stacks = 60
    stack_display = "number"

    async def apply(
        self,
        target: "Stats",
        attacker: Optional["Stats"] = None,
        damage: int = 0,
    ) -> None:
        entity_id = id(target)
        stack_attr = "_graygray_counter_maestro_stacks"

        if entity_id not in self._counter_stacks:
            self._counter_stacks[entity_id] = 0

        current_stacks = getattr(target, stack_attr, 0) + 1
        setattr(target, stack_attr, current_stacks)
        self._counter_stacks[entity_id] = current_stacks

        while current_stacks >= 40 and attacker is not None:
            self._counter_stacks[entity_id] -= 40
            setattr(target, stack_attr, self._counter_stacks[entity_id])
            await self._apply_damage_with_context(
                target,
                attacker,
                int(target.max_hp * 1.25),
                "Prime Counter Burst",
            )
            current_stacks = self._counter_stacks[entity_id]

        base_attack_buff = min(current_stacks, 50) * 0.07
        excess_stacks = max(0, current_stacks - 50)
        excess_attack_buff = excess_stacks * 0.04
        total_attack_multiplier = base_attack_buff + excess_attack_buff

        attack_buff = StatEffect(
            name=f"{self.id}_attack_stacks",
            stat_modifiers={"atk": int(target.atk * total_attack_multiplier)},
            duration=-1,
            source=self.id,
        )
        target.add_effect(attack_buff)

        mitigation_buff = StatEffect(
            name=f"{self.id}_mitigation_buff",
            stat_modifiers={"mitigation": 0.2},
            duration=1,
            source=self.id,
        )
        target.add_effect(mitigation_buff)

        if attacker is not None:
            await self.counter_attack(target, attacker, damage)

    async def counter_attack(self, defender: "Stats", attacker: "Stats", damage_received: int) -> None:
        if attacker is None:
            return

        counter_damage = int(damage_received * 0.75)
        await self._apply_damage_with_context(
            defender,
            attacker,
            counter_damage,
            "Prime Counter Attack",
        )

    @classmethod
    def get_description(cls) -> str:
        return (
            "[PRIME] Counters for 75% of damage taken and gains +7% attack per stack up to 50 (4% beyond). "
            "Bursts now trigger every 40 stacks for 125% max HP damage and grant 20% mitigation for a turn."
        )

