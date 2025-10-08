from dataclasses import dataclass
from dataclasses import field
from random import choice

from autofighter.character import CharacterType
from plugins.characters._base import PlayerBase
from plugins.damage_types import ALL_DAMAGE_TYPES
from plugins.damage_types import load_damage_type
from plugins.damage_types._base import DamageTypeBase


@dataclass
class Hilander(PlayerBase):
    id = "hilander"
    name = "Hilander"
    about = "A passionate brewmaster whose alchemical expertise extends far beyond tavern walls into the heat of battle. His critical ferment techniques create explosive combinations by treating combat like a complex brewing process—mixing elements, timing reactions, and achieving the perfect catalyst moment for devastating results. Hilander approaches each fight with the same methodical passion he brings to crafting the perfect ale, understanding that the right combination of pressure, timing, and elemental ingredients can create effects far greater than the sum of their parts. His battlefield brewery turns every engagement into an opportunity to perfect his most volatile recipes."
    char_type: CharacterType = CharacterType.A
    gacha_rarity = 5
    damage_type: DamageTypeBase = field(
        default_factory=lambda: load_damage_type(choice(ALL_DAMAGE_TYPES))
    )
    passives: list[str] = field(default_factory=lambda: ["hilander_critical_ferment"])
