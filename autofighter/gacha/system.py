from dataclasses import asdict
from dataclasses import dataclass
import random
from typing import Callable


@dataclass
class GachaConfig:
    base_rate: float
    pity_start: int
    pity_increment: float
    pity_threshold: int


@dataclass
class GachaSystem:
    config: GachaConfig
    pity_counter: int = 0

    def current_rate(self) -> float:
        if self.pity_counter >= self.config.pity_start:
            bonus = (
                self.pity_counter - self.config.pity_start + 1
            ) * self.config.pity_increment
            return min(1.0, self.config.base_rate + bonus)
        return self.config.base_rate

    def pull(self, rng: Callable[[], float] | None = None) -> bool:
        rng = rng or random.random
        if self.pity_counter >= self.config.pity_threshold:
            self.pity_counter = 0
            return True
        rate = self.current_rate()
        if rng() < rate:
            self.pity_counter = 0
            return True
        self.pity_counter += 1
        return False

    def to_dict(self) -> dict:
        return {"config": asdict(self.config), "pity_counter": self.pity_counter}

    @classmethod
    def from_dict(cls, data: dict) -> "GachaSystem":
        config = GachaConfig(**data["config"])
        return cls(config=config, pity_counter=data.get("pity_counter", 0))
