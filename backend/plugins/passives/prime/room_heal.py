from dataclasses import dataclass

from plugins.passives.normal.room_heal import RoomHeal


@dataclass
class RoomHealPrime(RoomHeal):
    """Prime variant of Room Heal with massive healing."""
    plugin_type = "passive"
    id = "room_heal_prime"
    name = "Prime Room Heal"
    trigger = "battle_end"
    amount = 5  # 5x base
    stack_display = "pips"

    @classmethod
    def get_description(cls) -> str:
        return (
            f"[PRIME] Heals {cls.amount} HP after each battle (5x). "
            f"Stacks display as {cls.stack_display}."
        )

