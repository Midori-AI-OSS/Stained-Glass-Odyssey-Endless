from __future__ import annotations

from dataclasses import dataclass

from plugins.effects import DebuffBase


@dataclass
class DefenseDown(DebuffBase):
    """Reduces defense to make foes more fragile."""

    id: str = "defense_down"
    name: str = "Defense Down"
    duration: int = 3
    max_stacks: int | None = 3
    amount: float = -35.0

    def __post_init__(self) -> None:
        super().__post_init__()
        self.stat_modifiers = {"defense": float(self.amount)}

    @classmethod
    def get_description(cls) -> str:
        return "Reduces defense with stacking copies for raid-style armor shreds."
