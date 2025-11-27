from __future__ import annotations

from dataclasses import dataclass

from plugins.effects import BuffBase


@dataclass
class DefenseUp(BuffBase):
    """Boost defense for survivability."""

    id: str = "defense_up"
    name: str = "Defense Up"
    duration: int = 4
    max_stacks: int | None = 5
    amount: float = 40.0

    def __post_init__(self) -> None:
        super().__post_init__()
        self.stat_modifiers = {"defense": float(self.amount)}

    @classmethod
    def get_description(cls) -> str:
        return "Raises defense, stacking up to five copies for prolonged protection."
