from dataclasses import dataclass

from plugins.passives.normal.player_level_up_bonus import PlayerLevelUpBonus


@dataclass
class PlayerLevelUpBonusGlitched(PlayerLevelUpBonus):
    """Glitched variant of Player's Enhanced Growth with doubled gains."""
    plugin_type = "passive"
    id = "player_level_up_bonus_glitched"
    name = "Glitched Enhanced Growth"
    trigger = "level_up"
    max_stacks = 1
    stack_display = "spinner"

    async def apply(self, target, new_level: int) -> None:
        """Apply enhanced level-up gains for Glitched Player (1.7x multiplier, doubled from 0.35 to 0.7).

        Args:
            target: Stats object receiving the bonus.
            new_level: The player's new level after leveling up.
        """
        from autofighter.stat_effect import StatEffect

        level_up_bonus = StatEffect(
            name=f"{self.id}_level_bonus",
            stat_modifiers={
                "max_hp": target.level_up_gains.get("max_hp", 10.0) * 0.7,
                "atk": target.level_up_gains.get("atk", 5.0) * 0.7,
                "defense": target.level_up_gains.get("defense", 3.0) * 0.7,
                "crit_rate": target.level_up_gains.get("crit_rate", 0.001) * 0.7,
                "crit_damage": target.level_up_gains.get("crit_damage", 0.05) * 0.7,
                "effect_hit_rate": target.level_up_gains.get("effect_hit_rate", 0.001) * 0.7,
                "mitigation": target.level_up_gains.get("mitigation", 0.01) * 0.7,
                "regain": target.level_up_gains.get("regain", 2.0) * 0.7,
                "dodge_odds": target.level_up_gains.get("dodge_odds", 0.001) * 0.7,
                "effect_resistance": target.level_up_gains.get("effect_resistance", 0.001) * 0.7,
                "vitality": target.level_up_gains.get("vitality", 0.01) * 0.7,
            },
            duration=-1,
            source=self.id,
        )
        target.add_effect(level_up_bonus)

    @classmethod
    def get_description(cls) -> str:
        return "[GLITCHED] Increases all level-up stat gains by 70% (doubled), enhancing growth to 1.7× the base amount."
