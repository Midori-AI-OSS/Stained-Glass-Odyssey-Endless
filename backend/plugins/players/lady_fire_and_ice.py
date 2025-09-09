from dataclasses import dataclass
from dataclasses import field
from random import choice

from autofighter.character import CharacterType
from plugins.damage_types import load_damage_type
from plugins.damage_types._base import DamageTypeBase
from plugins.players._base import PlayerBase


@dataclass
class LadyFireAndIce(PlayerBase):
    id = "lady_fire_and_ice"
    name = "LadyFireAndIce"
    about = "A legendary 6★ elemental master appearing to be 18-20 years old, whose reddish-blue hair reflects her dual nature. Living with Dissociative Schizophrenia, she experiences herself as two distinct elemental personas that work in perfect, devastating harmony. Her fire alignment runs so hot that she sleeps unclothed to manage the constant heat radiating from her body. In combat, her duality engine allows her to wield both fire and ice through seamless persona switches—one moment erupting with volcanic fury, the next freezing enemies with arctic precision. The opposing forces create devastating thermal shocks that few opponents can withstand."
    char_type: CharacterType = CharacterType.B
    gacha_rarity = 6
    damage_type: DamageTypeBase = field(
        default_factory=lambda: load_damage_type(choice(["Fire", "Ice"]))
    )
    passives: list[str] = field(
        default_factory=lambda: ["lady_fire_and_ice_duality_engine"]
    )
