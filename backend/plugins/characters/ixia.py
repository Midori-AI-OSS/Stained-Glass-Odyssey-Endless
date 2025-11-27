from dataclasses import dataclass
from dataclasses import field

from autofighter.character import CharacterType
from plugins.characters._base import PlayerBase
from plugins.damage_types import load_damage_type
from plugins.damage_types._base import DamageTypeBase


@dataclass
class Ixia(PlayerBase):
    id = "ixia"
    name = "Ixia"
    full_about = "A diminutive but fierce male lightning-wielder whose compact frame channels tremendous electrical energy. Despite his small stature, Ixia's tiny titan abilities allow him to unleash devastating electrical attacks that surge far beyond what his size would suggest. His lightning mastery makes him a formidable Type A combatant who proves that power isn't measured by physical dimensions but by the storm within."
    summarized_about = "A diminutive lightning-wielder who channels tremendous electrical power, proving that strength isn't measured by size."
    char_type: CharacterType = CharacterType.A
    gacha_rarity = 5
    damage_type: DamageTypeBase = field(
        default_factory=lambda: load_damage_type("Lightning")
    )
    passives: list[str] = field(default_factory=lambda: ["ixia_tiny_titan"])
    special_abilities: list[str] = field(
        default_factory=lambda: ["special.ixia.lightning_burst"]
    )
