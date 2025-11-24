from dataclasses import dataclass

from plugins.passives.normal.player_level_up_bonus import PlayerLevelUpBonus


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

    @classmethod
    def get_description(cls) -> str:
        return (
            "[GLITCHED] Doubles all stat gains from leveling up. "
            "Characters gain significantly more power per level. "
            "Experience requirements remain unchanged."
        )
