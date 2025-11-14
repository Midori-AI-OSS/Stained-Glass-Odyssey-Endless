from dataclasses import dataclass

from plugins.passives.normal.attack_up import AttackUp


@dataclass
class AttackUpPrime(AttackUp):
    """Prime variant of Attack Up with massive bonus."""
    plugin_type = "passive"
    id = "attack_up_prime"
    name = "Prime Attack Up"
    trigger = "battle_start"
    amount = 25  # 5x base for prime
    stack_display = "pips"

    @classmethod
    def get_description(cls) -> str:
        return (
            f"[PRIME] Grants +{cls.amount} attack at battle start (5x). "
            f"Stacks display as {cls.stack_display}."
        )

