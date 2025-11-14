from dataclasses import dataclass

from plugins.passives.normal.attack_up import AttackUp


@dataclass
class AttackUpBoss(AttackUp):
    """Boss variant of Attack Up with enhanced bonus."""
    plugin_type = "passive"
    id = "attack_up_boss"
    name = "Attack Up (Boss)"
    trigger = "battle_start"
    amount = 15  # 3x base for bosses
    stack_display = "pips"

    @classmethod
    def get_description(cls) -> str:
        return (
            f"[BOSS] Grants +{cls.amount} attack at battle start. "
            f"Stacks display as {cls.stack_display}."
        )

