from dataclasses import dataclass
from dataclasses import field
from random import choice

from autofighter.character import CharacterType
from plugins.damage_types import ALL_DAMAGE_TYPES
from plugins.damage_types import load_damage_type
from plugins.damage_types._base import DamageTypeBase
from plugins.characters._base import PlayerBase


@dataclass
class Graygray(PlayerBase):
    id = "graygray"
    name = "Graygray"
    about = "A tactical mastermind whose counter maestro abilities transform every enemy attack into a lesson in superior combat technique. Graygray doesn't just defend—she conducts battles like a symphony, turning opponent aggression into the very notes of their defeat. Her strategic brilliance lies in reading attack patterns and responding with perfectly timed counters that not only negate damage but convert that energy into devastating retaliations. Each strike against her becomes a teaching moment, as she demonstrates how true mastery lies not in overwhelming force, but in precise timing and flawless technique."
    char_type: CharacterType = CharacterType.B
    gacha_rarity = 5
    damage_type: DamageTypeBase = field(
        default_factory=lambda: load_damage_type(choice(ALL_DAMAGE_TYPES))
    )
    passives: list[str] = field(default_factory=lambda: ["graygray_counter_maestro"])
