from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import ClassVar

from autofighter.stats import StatEffect

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class LunaLunarReservoir:
    """Luna's Lunar Reservoir passive - charge-based system that scales attack count."""

    plugin_type = "passive"
    id = "luna_lunar_reservoir"
    name = "Lunar Reservoir"
    trigger = "action_taken"  # Triggers when Luna takes any action
    max_stacks = 200  # Show charge level 0-200
    stack_display = "number"

    # Class-level tracking of charge points for each entity
    _charge_points: ClassVar[dict[int, int]] = {}

    async def apply(self, target: "Stats") -> None:
        """Apply charge mechanics for Luna."""
        entity_id = id(target)

        # Initialize charge if not present
        if entity_id not in self._charge_points:
            self._charge_points[entity_id] = 0

        # Grant 1 charge point per action
        self._charge_points[entity_id] += 1
        current_charge = self._charge_points[entity_id]

        # Determine attack count based on charge level
        if current_charge < 35:
            target.actions_per_turn = 2
        elif current_charge < 50:
            target.actions_per_turn = 4
        elif current_charge < 70:
            target.actions_per_turn = 8
        elif current_charge < 85:
            target.actions_per_turn = 16
        else:  # 85+ charge
            target.actions_per_turn = 32

        # Soft cap bonus: each stack past 200 gives 0.025% dodge odds
        if current_charge > 200:
            stacks_past_soft_cap = current_charge - 200
            dodge_bonus = stacks_past_soft_cap * 0.00025  # 0.025% per stack

            dodge_effect = StatEffect(
                name=f"{self.id}_dodge_bonus",
                stat_modifiers={"dodge_odds": dodge_bonus},
                duration=-1,  # Permanent for rest of fight
                source=self.id,
            )
            target.add_effect(dodge_effect)

    async def on_turn_end(self, target: "Stats") -> None:
        """Handle charge spending at end of turn when in boosted mode."""
        entity_id = id(target)

        # Initialize charge if not present
        if entity_id not in self._charge_points:
            self._charge_points[entity_id] = 0
            return

        current_charge = self._charge_points[entity_id]

        # Spend 50 charge per turn when above 200 (boosted mode)
        if current_charge > 200:
            self._charge_points[entity_id] = max(200, current_charge - 50)

    @classmethod
    def get_charge(cls, target: "Stats") -> int:
        """Get current charge points for an entity."""
        return cls._charge_points.get(id(target), 0)

    @classmethod
    def add_charge(cls, target: "Stats", amount: int = 1) -> None:
        """Add charge points (for external effects)."""
        entity_id = id(target)
        if entity_id not in cls._charge_points:
            cls._charge_points[entity_id] = 0

        # Remove hard cap - allow unlimited stacking
        cls._charge_points[entity_id] += amount

    @classmethod
    def get_stacks(cls, target: "Stats") -> int:
        """Return current charge points for UI display."""
        return cls._charge_points.get(id(target), 0)

    @classmethod
    def get_display(cls, target: "Stats") -> str:
        """Display a spinner when charge is full and draining."""
        return "spinner" if cls.get_charge(target) >= 200 else "number"

    @classmethod
    def get_description(cls) -> str:
        return (
            "Gains 1 charge per action; attack count scales from 2 up to 32 at 85+ charge. "
            "Charge beyond 200 grants 0.025% dodge per point and drains 50 charge each turn."
        )
