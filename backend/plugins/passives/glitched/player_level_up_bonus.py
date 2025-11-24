from dataclasses import dataclass
from typing import TYPE_CHECKING

from autofighter.stat_effect import StatEffect
from plugins.passives.normal.player_level_up_bonus import PlayerLevelUpBonus

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class PlayerLevelUpBonusGlitched(PlayerLevelUpBonus):
    """[GLITCHED] Player Level Up Bonus - doubled stat gains.

    This glitched variant doubles all stat gains from leveling up,
    resulting in much faster character progression.
    """
    plugin_type = "passive"
    id = "player_level_up_bonus_glitched"
    name = "Glitched Level Up Bonus"
    trigger = "level_up"
    max_stacks = 1
    stack_display = "spinner"

    async def apply(self, target: "Stats", new_level: int) -> None:
        """Apply DOUBLED level-up gains (0.70 multiplier instead of 0.35)."""
        # DOUBLED: 70% bonus instead of 35%
        level_up_bonus = StatEffect(
            name=f"{self.id}_level_bonus",
            stat_modifiers={
                "max_hp": target.level_up_gains.get("max_hp", 10.0) * 0.70,  # Was 0.35
                "atk": target.level_up_gains.get("atk", 5.0) * 0.70,  # Was 0.35
                "defense": target.level_up_gains.get("defense", 3.0) * 0.70,  # Was 0.35
                "crit_rate": target.level_up_gains.get("crit_rate", 0.001) * 0.70,  # Was 0.35
                "crit_damage": target.level_up_gains.get("crit_damage", 0.05) * 0.70,  # Was 0.35
                "effect_hit_rate": target.level_up_gains.get("effect_hit_rate", 0.001) * 0.70,  # Was 0.35
                "mitigation": target.level_up_gains.get("mitigation", 0.01) * 0.70,  # Was 0.35
                "regain": target.level_up_gains.get("regain", 2.0) * 0.70,  # Was 0.35
                "dodge_odds": target.level_up_gains.get("dodge_odds", 0.001) * 0.70,  # Was 0.35
                "effect_resistance": target.level_up_gains.get("effect_resistance", 0.001) * 0.70,  # Was 0.35
                "vitality": target.level_up_gains.get("vitality", 0.01) * 0.70,  # Was 0.35
            },
            duration=-1,
            source=self.id,
        )
        target.add_effect(level_up_bonus)

    @classmethod
    def get_description(cls) -> str:
        return (
            "[GLITCHED] Increases all level-up stat gains by 70% (doubled), "
            "enhancing growth to 1.70× the base amount."
        )
