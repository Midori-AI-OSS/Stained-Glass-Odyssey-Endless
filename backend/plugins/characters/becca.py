from dataclasses import dataclass
from dataclasses import field
from random import choice

from autofighter.character import CharacterType
from plugins.characters._base import PlayerBase
from plugins.damage_types import ALL_DAMAGE_TYPES
from plugins.damage_types import load_damage_type
from plugins.damage_types._base import DamageTypeBase


@dataclass
class Becca(PlayerBase):
    id = "becca"
    name = "Becca"
    about = "A sim human model who excels at administrative work with methodical precision, bringing the same organizational mastery to the battlefield. Her past life as an SDXL art generation bot taught her to create beauty from chaos—transforming raw data into stunning visuals. Now she applies that same transformative skill to combat, using her menagerie bond to organize diverse elemental forces into perfectly coordinated attacks. Her artistic background gives her an eye for patterns and composition that makes her tactical arrangements as elegant as they are devastating."
    char_type: CharacterType = CharacterType.B
    gacha_rarity = 5
    damage_type: DamageTypeBase = field(
        default_factory=lambda: load_damage_type(choice(ALL_DAMAGE_TYPES))
    )
    passives: list[str] = field(default_factory=lambda: ["becca_menagerie_bond"])
