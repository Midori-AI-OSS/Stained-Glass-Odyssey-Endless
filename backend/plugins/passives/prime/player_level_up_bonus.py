from dataclasses import dataclass

from plugins.passives.normal.player_level_up_bonus import PlayerLevelUpBonus


@dataclass
class PlayerLevelUpBonusPrime(PlayerLevelUpBonus):
    """Prime variant of Player's Enhanced Growth with massive multiplier."""
    plugin_type = "passive"
    id = "player_level_up_bonus_prime"
    name = "Prime Enhanced Growth"
    trigger = "level_up"
    max_stacks = 1
    stack_display = "spinner"

    async def apply(self, target, new_level: int) -> None:
        """Apply enhanced level-up gains for Prime Player (4x multiplier).

        Args:
            target: Stats object receiving the bonus.
            new_level: The player's new level after leveling up.
        """
        from autofighter.stat_effect import StatEffect

        level_up_bonus = StatEffect(
            name=f"{self.id}_level_bonus",
            stat_modifiers={
                "max_hp": target.level_up_gains.get("max_hp", 10.0) * 3.0,
                "atk": target.level_up_gains.get("atk", 5.0) * 3.0,
                "defense": target.level_up_gains.get("defense", 3.0) * 3.0,
                "crit_rate": target.level_up_gains.get("crit_rate", 0.001) * 3.0,
                "crit_damage": target.level_up_gains.get("crit_damage", 0.05) * 3.0,
                "effect_hit_rate": target.level_up_gains.get("effect_hit_rate", 0.001) * 3.0,
                "mitigation": target.level_up_gains.get("mitigation", 0.01) * 3.0,
                "regain": target.level_up_gains.get("regain", 2.0) * 3.0,
                "dodge_odds": target.level_up_gains.get("dodge_odds", 0.001) * 3.0,
                "effect_resistance": target.level_up_gains.get("effect_resistance", 0.001) * 3.0,
                "vitality": target.level_up_gains.get("vitality", 0.01) * 3.0,
            },
            duration=-1,
            source=self.id,
        )
        target.add_effect(level_up_bonus)

    @classmethod
    def get_description(cls) -> str:
        return "[PRIME] Increases all level-up stat gains by 300%, enhancing growth to 4× the base amount."
