from dataclasses import dataclass
from typing import TYPE_CHECKING

from autofighter.stat_effect import StatEffect
from plugins.passives.normal.player_level_up_bonus import PlayerLevelUpBonus

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class PlayerLevelUpBonusPrime(PlayerLevelUpBonus):
    """[PRIME] Enhanced Growth doubled again for prime foes."""

    plugin_type = "passive"
    id = "player_level_up_bonus_prime"
    name = "Prime Growth"
    trigger = "level_up"
    max_stacks = 1
    stack_display = "spinner"

    async def apply(self, target: "Stats", new_level: int) -> None:
        bonus = StatEffect(
            name=f"{self.id}_level_bonus",
            stat_modifiers={
                key: value * 0.75
                for key, value in target.level_up_gains.items()
            },
            duration=-1,
            source=self.id,
        )
        target.add_effect(bonus)

    @classmethod
    def get_description(cls) -> str:
        return "[PRIME] Level-ups grant an additional 75% of every stat gain, stacking with Enhanced Growth."

