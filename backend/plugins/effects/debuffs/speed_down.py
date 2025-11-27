from __future__ import annotations

from dataclasses import dataclass

from plugins.effects import DebuffBase


@dataclass
class SpeedDown(DebuffBase):
    """Slows a target by reducing speed."""

    id: str = "speed_down"
    name: str = "Speed Down"
    duration: int = 2
    max_stacks: int | None = 2
    amount: float = -6.0

    def __post_init__(self) -> None:
        super().__post_init__()
        self.stat_modifiers = {"spd": float(self.amount)}

    @classmethod
    def get_description(cls) -> str:
        return "Applies a stacking slow effect that delays the target's turn order."
