from dataclasses import dataclass

from plugins.passives.normal.attack_up import AttackUp


@dataclass
class AttackUpGlitched(AttackUp):
    """Glitched variant of Attack Up with doubled bonus."""
    plugin_type = "passive"
    id = "attack_up_glitched"
    name = "Glitched Attack Up"
    trigger = "battle_start"
    amount = 10  # Doubled from base 5
    stack_display = "pips"

    @classmethod
    def get_description(cls) -> str:
        return (
            f"[GLITCHED] Grants +{cls.amount} attack at battle start (doubled). "
            f"Stacks display as {cls.stack_display}."
        )

