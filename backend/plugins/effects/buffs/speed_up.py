from __future__ import annotations

from dataclasses import dataclass

from plugins.effects import BuffBase


@dataclass
class SpeedUp(BuffBase):
    """Increases speed to take turns faster."""

    id: str = "speed_up"
    name: str = "Speed Up"
    duration: int = 2
    max_stacks: int | None = 3
    amount: float = 8.0

    def __post_init__(self) -> None:
        super().__post_init__()
        self.stat_modifiers = {"spd": float(self.amount)}

    @classmethod
    def get_description(cls) -> str:
        return "Provides a burst of speed, stacking three times for rapid action loops."
