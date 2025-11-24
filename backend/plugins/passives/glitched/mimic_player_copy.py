from dataclasses import dataclass

from plugins.passives.normal.mimic_player_copy import MimicPlayerCopy


@dataclass
class MimicPlayerCopyGlitched(MimicPlayerCopy):
    """[GLITCHED] Mimic Player Copy - doubled copy effectiveness.

    This glitched variant doubles the stat copying percentage and ability
    effectiveness when mimicking player characters, creating superior copies.
    """
    plugin_type = "passive"
    id = "mimic_player_copy_glitched"
    name = "Glitched Player Copy"
    trigger = "battle_start"
    max_stacks = 1
    stack_display = "spinner"

    @classmethod
    def get_description(cls) -> str:
        return (
            "[GLITCHED] Copies a player character with doubled stat percentage (200% instead of 100%). "
            "Inherits doubled ability power and passive effects. "
            "Maintains the copied identity throughout battle."
        )
