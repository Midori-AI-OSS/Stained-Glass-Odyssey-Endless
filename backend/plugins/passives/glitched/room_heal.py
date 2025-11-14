from dataclasses import dataclass

from plugins.passives.normal.room_heal import RoomHeal


@dataclass
class RoomHealGlitched(RoomHeal):
    """Glitched variant of Room Heal with doubled healing."""
    plugin_type = "passive"
    id = "room_heal_glitched"
    name = "Glitched Room Heal"
    trigger = "battle_end"
    amount = 2  # Doubled
    stack_display = "pips"

    @classmethod
    def get_description(cls) -> str:
        return (
            f"[GLITCHED] Heals {cls.amount} HP after each battle (doubled). "
            f"Stacks display as {cls.stack_display}."
        )

