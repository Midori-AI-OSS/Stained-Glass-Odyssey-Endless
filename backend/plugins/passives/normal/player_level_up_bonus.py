from dataclasses import dataclass
from typing import TYPE_CHECKING

from autofighter.stat_effect import StatEffect

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class PlayerLevelUpBonus:
    """Player's enhanced level-up gains passive."""
    plugin_type = "passive"
    id = "player_level_up_bonus"
    name = "Enhanced Growth"
    trigger = "level_up"  # Triggers when Player levels up
    max_stacks = 1  # Only one instance per character
    stack_display = "spinner"

    async def apply(self, target: "Stats", new_level: int) -> None:
        """Apply enhanced level-up gains for Player (1.35x multiplier).

        Args:
            target: Stats object receiving the bonus.
            new_level: The player's new level after leveling up.
        """
        level_up_bonus = StatEffect(
            name=f"{self.id}_level_bonus",
            stat_modifiers={
                "max_hp": target.level_up_gains.get("max_hp", 10.0) * 0.35,
                "atk": target.level_up_gains.get("atk", 5.0) * 0.35,
                "defense": target.level_up_gains.get("defense", 3.0) * 0.35,
                "crit_rate": target.level_up_gains.get("crit_rate", 0.001) * 0.35,
                "crit_damage": target.level_up_gains.get("crit_damage", 0.05) * 0.35,
                "effect_hit_rate": target.level_up_gains.get("effect_hit_rate", 0.001) * 0.35,
                "mitigation": target.level_up_gains.get("mitigation", 0.01) * 0.35,
                "regain": target.level_up_gains.get("regain", 2.0) * 0.35,
                "dodge_odds": target.level_up_gains.get("dodge_odds", 0.001) * 0.35,
                "effect_resistance": target.level_up_gains.get("effect_resistance", 0.001) * 0.35,
                "vitality": target.level_up_gains.get("vitality", 0.01) * 0.35,
            },
            duration=-1,
            source=self.id,
        )
        target.add_effect(level_up_bonus)

    @classmethod
    def get_description(cls) -> str:
        return "Increases all level-up stat gains by 35%, enhancing growth to 1.35× the base amount."
