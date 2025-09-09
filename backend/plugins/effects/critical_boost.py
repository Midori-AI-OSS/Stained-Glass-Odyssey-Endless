from dataclasses import dataclass
from dataclasses import field

from autofighter.stats import BUS
from autofighter.stats import Stats


@dataclass
class CriticalBoost:
    plugin_type = "effects"
    id = "critical_boost"

    crit_rate_per_stack: float = 0.005
    crit_damage_per_stack: float = 0.05
    stacks: int = 0
    target: Stats | None = field(default=None, init=False)

    @classmethod
    def get_description(cls) -> str:
        """Get the description of this effect for display purposes."""
        return (
            "+0.5% crit rate and +5% crit damage per stack. Removed when taking damage."
        )

    def apply(self, target: Stats) -> None:
        if self.target is None:
            self.target = target
            BUS.subscribe("damage_taken", self._on_damage_taken)
        self.stacks += 1
        target._base_crit_rate += self.crit_rate_per_stack
        target._base_crit_damage += self.crit_damage_per_stack
        BUS.emit("critical_boost_change", target, self.stacks)

    def _on_damage_taken(self, victim: Stats, *_: object) -> None:
        if victim is not self.target or self.target is None or self.stacks == 0:
            return
        self.target._base_crit_rate -= self.crit_rate_per_stack * self.stacks
        self.target._base_crit_damage -= self.crit_damage_per_stack * self.stacks
        self.stacks = 0
        BUS.emit("critical_boost_change", victim, 0)
        BUS.unsubscribe("damage_taken", self._on_damage_taken)
        self.target = None
