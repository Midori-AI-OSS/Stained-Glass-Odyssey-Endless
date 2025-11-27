from dataclasses import dataclass
from typing import TYPE_CHECKING

from autofighter.stat_effect import StatEffect
from plugins.passives.normal.player_level_up_bonus import PlayerLevelUpBonus

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class PlayerLevelUpBonusBoss(PlayerLevelUpBonus):
    """Boss-tier level bonus that adds 52.5% to level-up gains."""

    plugin_type = "passive"
    id = "player_level_up_bonus_boss"
    name = "Level Up Bonus (Boss)"
    trigger = "level_up"
    max_stacks = 1
    stack_display = "spinner"

    async def apply(self, target: "Stats", new_level: int) -> None:
        multiplier = 0.525
        gains = target.level_up_gains
        level_up_bonus = StatEffect(
            name=f"{self.id}_level_bonus",
            stat_modifiers={
                "max_hp": gains.get("max_hp", 10.0) * multiplier,
                "atk": gains.get("atk", 5.0) * multiplier,
                "defense": gains.get("defense", 3.0) * multiplier,
                "crit_rate": gains.get("crit_rate", 0.001) * multiplier,
                "crit_damage": gains.get("crit_damage", 0.05) * multiplier,
                "effect_hit_rate": gains.get("effect_hit_rate", 0.001) * multiplier,
                "mitigation": gains.get("mitigation", 0.01) * multiplier,
                "regain": gains.get("regain", 2.0) * multiplier,
                "dodge_odds": gains.get("dodge_odds", 0.001) * multiplier,
                "effect_resistance": gains.get("effect_resistance", 0.001) * multiplier,
                "vitality": gains.get("vitality", 0.01) * multiplier,
            },
            duration=-1,
            source=self.id,
        )
        target.add_effect(level_up_bonus)

    @classmethod
    def get_description(cls) -> str:
        return "[BOSS] Increases all level-up stat gains by 52.5%, offering more growth than normal foes but less than glitched tiers."
