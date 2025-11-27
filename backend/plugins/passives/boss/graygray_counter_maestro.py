from dataclasses import dataclass
from typing import TYPE_CHECKING

from plugins.passives.normal.graygray_counter_maestro import GraygrayCounterMaestro

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class GraygrayCounterMaestroBoss(GraygrayCounterMaestro):
    """Boss Counter Maestro that retaliates for 75% of damage taken."""

    plugin_type = "passive"
    id = "graygray_counter_maestro_boss"
    name = "Counter Maestro (Boss)"
    trigger = "damage_taken"
    max_stacks = 50
    stack_display = "number"

    async def counter_attack(self, defender: "Stats", attacker: "Stats", damage_received: int) -> None:
        """Retaliate for 1.5× the normal return damage."""

        if attacker is None:
            return

        counter_damage = int(damage_received * 0.75)
        await self._apply_damage_with_context(
            defender,
            attacker,
            counter_damage,
            "Boss Counter Attack",
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
            "[BOSS] Counterattacks return 75% of damage taken and otherwise follow Counter Maestro's stacking rules."
        )
