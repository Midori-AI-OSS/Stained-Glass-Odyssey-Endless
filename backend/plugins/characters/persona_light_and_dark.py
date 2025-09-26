from dataclasses import dataclass
from dataclasses import field
from random import choice

from autofighter.character import CharacterType
from plugins.damage_types import load_damage_type
from plugins.damage_types._base import DamageTypeBase
from plugins.characters._base import PlayerBase


@dataclass
class PersonaLightAndDark(PlayerBase):
    id = "persona_light_and_dark"
    name = "PersonaLightAndDark"
    about = (
        "A 6★ guardian and brother to Lady Light and Lady Darkness, Persona Light and Dark fights to keep "
        "his sisters safe. He speaks only the radiant glyphs of the Light tongue, letting sweeping gestures "
        "and twin halos translate his intent. By trading between the family's luminous ward and shadow bastion, "
        "he drags enemy focus onto himself while sheltering the people he protects."
    )
    char_type: CharacterType = CharacterType.A
    gacha_rarity = 6
    damage_type: DamageTypeBase = field(
        default_factory=lambda: load_damage_type(choice(["Light", "Dark"]))
    )
    passives: list[str] = field(
        default_factory=lambda: ["persona_light_and_dark_duality"]
    )
