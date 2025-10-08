from dataclasses import dataclass
from dataclasses import field
from random import choice

from autofighter.character import CharacterType
from plugins.characters._base import PlayerBase
from plugins.damage_types import ALL_DAMAGE_TYPES
from plugins.damage_types import load_damage_type
from plugins.damage_types._base import DamageTypeBase


@dataclass
class Mezzy(PlayerBase):
    id = "mezzy"
    name = "Mezzy"
    about = "A voracious defender whose gluttonous bulwark represents the ultimate expression of 'what doesn't kill you makes you stronger.' Mezzy literally devours enemy attacks, her unique physiology converting incoming damage into raw power that fuels her own abilities. The more her opponents throw at her, the stronger she becomes—creating a terrifying feedback loop where every assault just makes her hungrier for more. Her combat style revolves around tanking massive amounts of damage while growing exponentially more dangerous, turning what should be weakening blows into a feast that only strengthens her resolve and fighting capability."
    char_type: CharacterType = CharacterType.B
    gacha_rarity = 5
    damage_type: DamageTypeBase = field(
        default_factory=lambda: load_damage_type(choice(ALL_DAMAGE_TYPES))
    )
    passives: list[str] = field(default_factory=lambda: ["mezzy_gluttonous_bulwark"])
