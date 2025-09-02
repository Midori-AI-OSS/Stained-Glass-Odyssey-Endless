from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import ClassVar

from autofighter.stats import StatEffect

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class BubblesBubbleBurst:
    """Bubbles' Bubble Burst passive - random element with area damage."""
    plugin_type = "passive"
    id = "bubbles_bubble_burst"
    name = "Bubble Burst"
    trigger = "turn_start"  # Triggers at start of Bubbles' turn
    max_stacks = 20  # Soft cap - show attack buff stacks with diminished returns past 20

    # Track bubble stacks per enemy target
    _bubble_stacks: ClassVar[dict[int, dict[int, int]]] = {}  # bubbles_id -> {target_id -> stacks}

    async def apply(self, target: "Stats") -> None:
        """Apply Bubbles' random element switching mechanics."""
        # Switch damage type randomly each turn
        import random

        # Available damage types (simplified - in full implementation would use actual damage type system)
        damage_types = ["fire", "ice", "lightning", "earth", "wind", "dark", "light"]
        new_type = random.choice(damage_types)

        # Store current damage type for area damage calculation
        setattr(target, "_bubbles_current_element", new_type)

        # In a full implementation, this would actually change target.damage_type
        # For now, we'll track it for the burst effect

    async def on_hit_enemy(self, bubbles: "Stats", enemy: "Stats") -> None:
        """Apply bubble stack when hitting an enemy."""
        bubbles_id = id(bubbles)
        enemy_id = id(enemy)

        # Initialize tracking
        if bubbles_id not in self._bubble_stacks:
            self._bubble_stacks[bubbles_id] = {}
        if enemy_id not in self._bubble_stacks[bubbles_id]:
            self._bubble_stacks[bubbles_id][enemy_id] = 0

        # Add bubble stack
        self._bubble_stacks[bubbles_id][enemy_id] += 1

        # Check if we've reached 3 stacks for area burst
        if self._bubble_stacks[bubbles_id][enemy_id] >= 3:
            await self._trigger_bubble_burst(bubbles, enemy)

    async def _trigger_bubble_burst(self, bubbles: "Stats", trigger_enemy: "Stats") -> None:
        """Trigger bubble burst area damage and effects."""
        bubbles_id = id(bubbles)
        trigger_enemy_id = id(trigger_enemy)

        # Reset bubble stacks for this enemy
        if bubbles_id in self._bubble_stacks and trigger_enemy_id in self._bubble_stacks[bubbles_id]:
            self._bubble_stacks[bubbles_id][trigger_enemy_id] = 0

        # Grant Bubbles permanent attack buff with soft cap logic (reasonable addition)
        current_stacks = len([e for e in bubbles._active_effects if 'burst_bonus' in e.name])

        # Determine buff strength - soft cap at 20 stacks (diminished returns after)
        if current_stacks >= 20:
            # Past soft cap: reduced effectiveness (5% instead of 10%)
            attack_buff_multiplier = 0.05
        else:
            # Normal effectiveness per planning doc
            attack_buff_multiplier = 0.1

        attack_buff = StatEffect(
            name=f"{self.id}_burst_bonus_{current_stacks}",
            stat_modifiers={"atk": int(bubbles.atk * attack_buff_multiplier)},
            duration=-1,  # Permanent
            source=self.id,
        )
        bubbles.add_effect(attack_buff)

        # Area damage to all combatants (would need battle system integration)
        # This should deal area damage of the last element used to all combatants
        # current_element = getattr(bubbles, "_bubbles_current_element", "generic")

        # Apply DoT of that element to enemies (would need enemy targeting)
        # Planning doc: "leaving a two-turn DoT of that element on enemies"

        # Reset damage type for next turn (planning doc requirement)
        setattr(bubbles, "_bubbles_current_element", None)

    @classmethod
    def get_bubble_stacks(cls, bubbles: "Stats", enemy: "Stats") -> int:
        """Get current bubble stacks on a specific enemy."""
        bubbles_id = id(bubbles)
        enemy_id = id(enemy)

        if bubbles_id not in cls._bubble_stacks:
            return 0
        return cls._bubble_stacks[bubbles_id].get(enemy_id, 0)

    @classmethod
    def get_stacks(cls, target: "Stats") -> int:
        """Return current attack buff stacks for UI display."""
        # Count permanent attack buff effects from bubble bursts
        return len([e for e in target._active_effects if e.name.startswith(f"{cls.id}_burst_bonus")])

    @classmethod
    def get_attack_buff_stacks(cls, target: "Stats") -> int:
        """Get current number of permanent attack buffs from bubble bursts."""
        return cls.get_stacks(target)
