from dataclasses import dataclass
from dataclasses import field
from dataclasses import fields

from plugins.damage_types import random_damage_type
from plugins.damage_types._base import DamageTypeBase
from plugins.foes._base import FoeBase


@dataclass
class Slime(FoeBase):
    id = "slime"
    name = "Slime"
    prompt: str = "Foe prompt placeholder"
    about: str = "Foe description placeholder"
    damage_type: DamageTypeBase = field(default_factory=random_damage_type)
    # Allow battle scaling to respect a lower minimum defense specifically for Slime
    min_defense_override: int = 0

    def __post_init__(self) -> None:
        super().__post_init__()

        scale = 0.1
        base_stats = {
            "max_hp",
            "atk",
            "defense",
            "crit_rate",
            "crit_damage",
            "effect_hit_rate",
            "mitigation",
            "regain",
            "dodge_odds",
            "effect_resistance",
            "vitality",
        }

        for dataclass_field in fields(FoeBase):
            name = dataclass_field.name
            if name.startswith("_base_"):
                continue

            value = getattr(self, name)
            if not isinstance(value, (int, float)):
                continue

            scaled_value = type(value)(value * scale)

            if name in base_stats:
                self.set_base_stat(name, scaled_value)

            setattr(self, name, scaled_value)

        if isinstance(getattr(self, "max_hp", None), (int, float)):
            self.hp = type(self.hp)(getattr(self, "max_hp"))

        defense_base = self.get_base_stat("defense")
        if isinstance(defense_base, (int, float)):
            reduced_defense = int(defense_base * scale)
            self.set_base_stat("defense", reduced_defense)
            setattr(self, "defense", reduced_defense)
