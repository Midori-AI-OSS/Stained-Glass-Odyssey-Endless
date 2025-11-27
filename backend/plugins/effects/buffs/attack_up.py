from __future__ import annotations

from dataclasses import dataclass

from plugins.effects import BuffBase


@dataclass
class AttackUp(BuffBase):
    """Flat attack bonus for a few turns."""

    id: str = "attack_up"
    name: str = "Attack Up"
    duration: int = 3
    stack_display: str = "number"
    max_stacks: int | None = 5
    amount: float = 35.0

    def __post_init__(self) -> None:
        super().__post_init__()
        self.stat_modifiers = {"atk": float(self.amount)}

    @classmethod
    def get_description(cls) -> str:
        return "Temporarily increases attack by a flat amount and stacks up to five times."
