from __future__ import annotations

from dataclasses import dataclass

from plugins.effects import DebuffBase


@dataclass
class AttackDown(DebuffBase):
    """Lowers attack power for the effect duration."""

    id: str = "attack_down"
    name: str = "Attack Down"
    duration: int = 3
    max_stacks: int | None = 3
    amount: float = -30.0

    def __post_init__(self) -> None:
        super().__post_init__()
        self.stat_modifiers = {"atk": float(self.amount)}

    @classmethod
    def get_description(cls) -> str:
        return "Reduces attack in flat values; up to three stacks can cripple heavy hitters."
