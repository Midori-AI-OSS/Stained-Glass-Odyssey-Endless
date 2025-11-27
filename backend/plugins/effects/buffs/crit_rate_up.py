from __future__ import annotations

from dataclasses import dataclass

from plugins.effects import BuffBase


@dataclass
class CritRateUp(BuffBase):
    """Increases critical hit chance."""

    id: str = "crit_rate_up"
    name: str = "Critical Rate Up"
    duration: int = 3
    max_stacks: int | None = 4
    amount: float = 0.05

    def __post_init__(self) -> None:
        super().__post_init__()
        self.stat_modifiers = {"crit_rate": float(self.amount)}

    @classmethod
    def get_description(cls) -> str:
        return "Adds +5% crit rate per stack for reliable critical windows."
