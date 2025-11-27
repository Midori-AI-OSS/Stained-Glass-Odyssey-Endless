from dataclasses import dataclass
from typing import TYPE_CHECKING

from plugins.passives.normal.ally_overload import AllyOverload

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class AllyOverloadGlitched(AllyOverload):
    """[GLITCHED] Ally's Overload - twin dagger stance with doubled charge gains.

    This glitched variant doubles charge gain (20 per action instead of 10) and
    maintains the same Overload mechanics, allowing for more frequent activation
    of the enhanced stance but with the same risks and benefits.
    """
    plugin_type = "passive"
    id = "ally_overload_glitched"
    name = "Glitched Overload"
    trigger = "action_taken"
    max_stacks = 240  # Doubled soft cap to match doubled gains
    stack_display = "number"

    async def apply(self, target: "Stats") -> None:
        """Apply Ally's twin dagger and overload mechanics with doubled charge gain."""
        entity_id = id(target)

        # Initialize if not present
        if entity_id not in self._overload_charge:
            self._overload_charge[entity_id] = 0
            self._overload_active[entity_id] = False

        # Twin daggers - always grants two attacks per action
        if not self._overload_active[entity_id]:
            target.actions_per_turn = 2

        # Build DOUBLED 20 Overload charge per pair of strikes (was 10)
        base_charge_gain = 20  # Doubled

        # Soft cap: past 240, gain charge at reduced rate (50% effectiveness)
        current_charge = self._overload_charge[entity_id]
        if current_charge > 240:  # Doubled threshold
            charge_gain = base_charge_gain * 0.5  # Diminished returns
        else:
            charge_gain = base_charge_gain

        self._overload_charge[entity_id] += charge_gain

        # Check if Overload can be triggered (100+ charge)
        current_charge = self._overload_charge[entity_id]
        if current_charge >= 100 and not self._overload_active[entity_id]:
            # Can activate Overload stance
            await self._activate_overload(target)

        # Handle charge decay when stance is inactive
        if not self._overload_active[entity_id]:
            self._overload_charge[entity_id] = max(0, current_charge - 5)

    @classmethod
    def get_description(cls) -> str:
        return (
            "[GLITCHED] Twin daggers grant two attacks per action and build 20 charge (doubled), "
            "decaying by 5 when inactive. At 100 charge, Overload activates: attack count doubles again, "
            "damage +30%, and damage taken +40%, draining 20 charge per turn. Charge gain halves above 240."
        )
