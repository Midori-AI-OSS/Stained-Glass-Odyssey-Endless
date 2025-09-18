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

        scaled_numeric: dict[str, int | float] = {}
        scaled_base_stats: dict[str, int | float] = {}

        for dataclass_field in fields(type(self)):
            name = dataclass_field.name
            if name.startswith("_base_"):
                continue

            value = getattr(self, name)
            if not isinstance(value, (int, float)):
                continue

            scaled_value = type(value)(value * scale)
            scaled_numeric[name] = scaled_value

            if name in base_stats:
                scaled_base_stats[name] = scaled_value

        super().__post_init__()

        for stat_name, scaled_value in scaled_base_stats.items():
            self.set_base_stat(stat_name, scaled_value)

        for name, scaled_value in scaled_numeric.items():
            setattr(self, name, scaled_value)

        max_hp_value = getattr(self, "max_hp", None)
        if isinstance(max_hp_value, (int, float)):
            current_hp = getattr(self, "hp", max_hp_value)
            setattr(self, "hp", type(current_hp)(max_hp_value))
