from __future__ import annotations

from dataclasses import dataclass

from plugins.effects import DebuffBase


@dataclass
class Blind(DebuffBase):
    """Cuts effect hit rate to make status applications miss."""

    id: str = "blind"
    name: str = "Blind"
    duration: int = 2
    max_stacks: int | None = 2
    amount: float = -0.4

    def __post_init__(self) -> None:
        super().__post_init__()
        self.stat_modifiers = {"effect_hit_rate": float(self.amount)}

    @classmethod
    def get_description(cls) -> str:
        return "Reduces effect hit rate by 40% per stack, limiting DoT and debuff uptime."
