from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import ClassVar
from typing import Optional

from autofighter.stat_effect import StatEffect

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class GraygrayCounterMaestro:
    """Graygray's Counter Maestro passive - retaliates after every hit taken."""
    plugin_type = "passive"
    id = "graygray_counter_maestro"
    name = "Counter Maestro"
    trigger = "damage_taken"  # Triggers when Graygray takes damage
    max_stacks = 50  # Soft cap - show counter attack stacks with diminished returns past 50
    stack_display = "number"

    # Track successful counter attacks for +5% attack stacks
    _counter_stacks: ClassVar[dict[int, int]] = {}

    async def apply(
        self,
        target: "Stats",
        attacker: Optional["Stats"] = None,
        damage: int = 0,
    ) -> None:
        """Apply counter-attack mechanics for Graygray and retaliate."""
        entity_id = id(target)

        # Initialize counter stack tracking if not present
        if entity_id not in self._counter_stacks:
            self._counter_stacks[entity_id] = 0

        # Increment counter stacks (each successful counter grants attack bonus)
        self._counter_stacks[entity_id] += 1
        current_stacks = self._counter_stacks[entity_id]

        # Unleash burst damage for every 50 stacks accumulated
        while current_stacks >= 50 and attacker is not None:
            self._counter_stacks[entity_id] -= 50
            await attacker.apply_damage(
                target.max_hp,
                attacker=target,
                trigger_on_hit=False,
                action_name="Counter Maestro Burst",
            )
            current_stacks = self._counter_stacks[entity_id]

        # Apply cumulative attack buff with soft cap logic
        # First 50 stacks: +5% attack per stack
        # Stacks past 50: +2.5% attack per stack (diminished returns)
        base_attack_buff = min(current_stacks, 50) * 0.05
        excess_stacks = max(0, current_stacks - 50)
        excess_attack_buff = excess_stacks * 0.025

        total_attack_multiplier = base_attack_buff + excess_attack_buff

        attack_buff = StatEffect(
            name=f"{self.id}_attack_stacks",
            stat_modifiers={"atk": int(target.atk * total_attack_multiplier)},
            duration=-1,  # Permanent for rest of fight
            source=self.id,
        )
        target.add_effect(attack_buff)

        # Grant mitigation buff for one turn
        mitigation_buff = StatEffect(
            name=f"{self.id}_mitigation_buff",
            stat_modifiers={"mitigation": 0.1},  # 10% mitigation increase
            duration=1,  # One turn
            source=self.id,
        )
        target.add_effect(mitigation_buff)

        # Retaliate after applying buffs
        if attacker is not None:
            await self.counter_attack(target, attacker, damage)

    async def counter_attack(self, defender: "Stats", attacker: "Stats", damage_received: int) -> None:
        """Perform the actual counter attack."""
        if attacker is None:
            return

        # Deal 50% of damage received back to attacker
        counter_damage = int(damage_received * 0.5)

        # Use defender's current damage type for the counter
        await attacker.apply_damage(
            counter_damage,
            attacker=defender,
            trigger_on_hit=False,  # Avoid recursive triggers
            action_name="Counter Attack"
        )

    @classmethod
    def get_stacks(cls, target: "Stats") -> int:
        """Return current counter stacks for UI display."""
        return cls._counter_stacks.get(id(target), 0)

    @classmethod
    def get_description(cls) -> str:
        return (
            "Counterattacks whenever hit, dealing 50% of damage received. "
            "Each counter grants +5% attack up to 50 stacks, then +2.5% beyond, "
            "and provides 10% mitigation for one turn. At 50 stacks, unleashes a burst for max HP damage."
        )
