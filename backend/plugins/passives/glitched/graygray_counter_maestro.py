from dataclasses import dataclass
from typing import TYPE_CHECKING

from plugins.passives.normal.graygray_counter_maestro import GraygrayCounterMaestro

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class GraygrayCounterMaestroGlitched(GraygrayCounterMaestro):
    """[GLITCHED] Graygray's Counter Maestro - counter with doubled damage.

    This glitched variant doubles the counter attack damage (100% of damage received
    instead of 50%) while maintaining the same attack stacking mechanics and burst
    damage threshold at 50 stacks.
    """
    plugin_type = "passive"
    id = "graygray_counter_maestro_glitched"
    name = "Glitched Counter Maestro"
    trigger = "damage_taken"
    max_stacks = 50
    stack_display = "number"

    async def counter_attack(self, defender: "Stats", attacker: "Stats", damage_received: int) -> None:
        """Perform counter attack with DOUBLED damage (100% instead of 50%)."""
        if attacker is None:
            return

        # DOUBLED counter damage (100% of damage received)
        counter_damage = damage_received  # Doubled from int(damage_received * 0.5)

        await self._apply_damage_with_context(
            defender,
            attacker,
            counter_damage,
            "Glitched Counter Attack",
        )

        try:
            from autofighter.rooms.battle.pacing import impact_pause as _impact_pause
        except ModuleNotFoundError:
            _impact_pause = None

        if _impact_pause is not None:
            await _impact_pause(defender, 1)

    @classmethod
    def get_description(cls) -> str:
        return (
            "[GLITCHED] Counterattacks whenever hit, dealing 100% of damage received (doubled). "
            "Each counter grants +5% attack up to 50 stacks, then +2.5% beyond, "
            "and provides 10% mitigation for one turn. At 50 stacks, unleashes a burst for max HP damage."
        )
