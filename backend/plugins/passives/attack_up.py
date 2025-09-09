from dataclasses import dataclass

from autofighter.stats import StatEffect


@dataclass
class AttackUp:
    plugin_type = "passive"
    id = "attack_up"
    name = "Attack Up"
    trigger = "battle_start"
    amount = 5
    stack_display = "pips"

    async def apply(self, target, **kwargs) -> None:
        stack_index = kwargs.get("stack_index", 0)
        effect = StatEffect(
            name=f"{self.id}_atk_up_{stack_index}",
            stat_modifiers={"atk": self.amount},
            source=self.id,
        )
        target.add_effect(effect)

    @classmethod
    def get_description(cls) -> str:
        return (
            f"Grants +{cls.amount} attack at battle start. "
            f"Stacks display as {cls.stack_display}."
        )
