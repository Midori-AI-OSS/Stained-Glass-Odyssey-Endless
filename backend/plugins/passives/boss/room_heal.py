from dataclasses import dataclass

from plugins.passives.normal.room_heal import RoomHeal


@dataclass
class RoomHealBoss(RoomHeal):
    """Boss variant of Room Heal with enhanced healing."""
    plugin_type = "passive"
    id = "room_heal_boss"
    name = "Room Heal (Boss)"
    trigger = "battle_end"
    amount = 3  # 3x base
    stack_display = "pips"

    @classmethod
    def get_description(cls) -> str:
        return (
            f"[BOSS] Heals {cls.amount} HP after each battle. "
            f"Stacks display as {cls.stack_display}."
        )

