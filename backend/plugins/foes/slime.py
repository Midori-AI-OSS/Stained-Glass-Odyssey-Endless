from dataclasses import dataclass
from dataclasses import field

from autofighter.rooms.foes.scaling import apply_permanent_scaling
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
        apply_permanent_scaling(
            self,
            multipliers={
                "max_hp": scale,
                "atk": scale,
                "defense": scale,
                "crit_rate": scale,
                "crit_damage": scale,
                "effect_hit_rate": scale,
                "mitigation": scale,
                "regain": scale,
                "dodge_odds": scale,
                "effect_resistance": scale,
                "vitality": scale,
            },
            name="Slime baseline",
            modifier_id="slime_baseline",
        )
        self.hp = self.max_hp
