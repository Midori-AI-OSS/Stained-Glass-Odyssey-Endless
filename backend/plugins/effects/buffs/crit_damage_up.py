from __future__ import annotations

from dataclasses import dataclass

from plugins.effects import BuffBase


@dataclass
class CritDamageUp(BuffBase):
    """Increases critical strike damage."""

    id: str = "crit_damage_up"
    name: str = "Critical Damage Up"
    duration: int = 3
    max_stacks: int | None = 3
    amount: float = 0.2

    def __post_init__(self) -> None:
        super().__post_init__()
        self.stat_modifiers = {"crit_damage": float(self.amount)}

    @classmethod
    def get_description(cls) -> str:
        return "Boosts critical damage by 20% per stack to amplify burst turns."
