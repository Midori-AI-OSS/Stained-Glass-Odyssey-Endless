from dataclasses import dataclass
from dataclasses import field
from random import choice

from autofighter.character import CharacterType
from plugins.characters._base import PlayerBase
from plugins.damage_types import ALL_DAMAGE_TYPES
from plugins.damage_types import load_damage_type
from plugins.damage_types._base import DamageTypeBase


@dataclass
class Bubbles(PlayerBase):
    id = "bubbles"
    name = "Bubbles"
    about = "An enthusiastic aquatic fighter whose bubbly personality masks a devastating combat style built around explosive chain reactions. His bubble burst abilities create cascading detonations that spread across the battlefield like underwater fireworks—each burst triggering additional explosions in a symphony of aquatic destruction. With boundless energy and an infectious optimism, Bubbles approaches every battle like a game, but his seemingly playful attacks pack tremendous force. His mastery of pressure dynamics allows him to create bubble formations that can both shield allies and devastate enemies when they inevitably pop."
    char_type: CharacterType = CharacterType.A
    gacha_rarity = 5
    damage_type: DamageTypeBase = field(
        default_factory=lambda: load_damage_type(choice(ALL_DAMAGE_TYPES))
    )
    passives: list[str] = field(default_factory=lambda: ["bubbles_bubble_burst"])
