from dataclasses import dataclass


@dataclass
class RoomHeal:
    plugin_type = "passive"
    id = "room_heal"
    name = "Room Heal"
    trigger = "battle_end"
    amount = 1
    stack_display = "pips"

    async def apply(self, target, **kwargs) -> None:
        # Support monkeypatching: if class attribute differs from original default, use class attribute
        heal_amount = type(self).amount if type(self).amount != 1 else self.amount
        await target.apply_healing(heal_amount)

    @classmethod
    def get_description(cls) -> str:
        return (
            f"Heals {cls.amount} HP after each battle. "
            f"Stacks display as {cls.stack_display}."
        )
