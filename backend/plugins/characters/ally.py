from dataclasses import dataclass
from dataclasses import field
from random import choice

from autofighter.character import CharacterType
from plugins.characters._base import PlayerBase
from plugins.damage_types import ALL_DAMAGE_TYPES
from plugins.damage_types import load_damage_type
from plugins.damage_types._base import DamageTypeBase


@dataclass
class Ally(PlayerBase):
    id = "ally"
    name = "Ally"
    about = "A versatile support fighter whose tactical brilliance shines through her overload capabilities, systematically dismantling enemy defenses through strategic elemental manipulation. Known for her uncanny adaptability, Ally reads the battlefield like a chess master, identifying weak points in enemy formations and exploiting them with perfectly timed elemental strikes. Her mastery spans all damage types, allowing her to adapt her combat style to counter any opponent. In combat, she excels at overloading enemy systems—disrupting their magical circuits, overwhelming their defenses, and creating cascade failures that turn their own power against them."
    char_type: CharacterType = CharacterType.B
    gacha_rarity = 5
    damage_type: DamageTypeBase = field(
        default_factory=lambda: load_damage_type(choice(ALL_DAMAGE_TYPES))
    )
    passives: list[str] = field(default_factory=lambda: ["ally_overload"])
