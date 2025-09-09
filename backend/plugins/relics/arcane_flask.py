from dataclasses import dataclass
from dataclasses import field

from autofighter.stats import BUS
from plugins.relics._base import RelicBase
from plugins.relics._base import safe_async_task


@dataclass
class ArcaneFlask(RelicBase):
    """After an Ultimate, grant a shield equal to 20% Max HP per stack."""

    id: str = "arcane_flask"
    name: str = "Arcane Flask"
    stars: int = 2
    effects: dict[str, float] = field(default_factory=dict)
    about: str = "After an Ultimate, grant a shield equal to 20% Max HP."

    def apply(self, party) -> None:
        super().apply(party)

        stacks = party.relics.count(self.id)

        def _ultimate(user) -> None:
            user.enable_overheal()  # Enable shields for the user
            shield = int(user.max_hp * 0.2 * stacks)

            # Track the shield generation
            BUS.emit(
                "relic_effect",
                "arcane_flask",
                user,
                "shield_granted",
                shield,
                {
                    "shield_percentage": 20 * stacks,
                    "max_hp": user.max_hp,
                    "trigger": "ultimate_used",
                    "stacks": stacks,
                },
            )

            safe_async_task(user.apply_healing(shield))

        BUS.subscribe("ultimate_used", _ultimate)

    def describe(self, stacks: int) -> str:
        pct = 20 * stacks
        return f"After an Ultimate, grant a shield equal to {pct}% Max HP."
