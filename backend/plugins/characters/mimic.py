from dataclasses import dataclass
from dataclasses import field
from random import choice
from typing import ClassVar

from autofighter.character import CharacterType
from plugins.characters._base import PlayerBase
from plugins.damage_types import ALL_DAMAGE_TYPES
from plugins.damage_types import load_damage_type
from plugins.damage_types._base import DamageTypeBase


@dataclass
class Mimic(PlayerBase):
    id = "mimic"
    name = "Mimic"
    about = "A mysterious shapeshifter whose true form remains unknown, existing as a perfect reflection of whatever combat style it encounters. Its player copy ability allows it to flawlessly replicate not just the appearance but the entire fighting methodology of any opponent, creating an unsettling mirror match where enemies face their own techniques turned against them. Mimic doesn't just adapt to combat situations—it becomes them, transforming into the ideal counter for whatever challenge it faces. This ultimate adaptability makes it both invaluable as an ally and terrifying as an opponent, as it can become anyone's perfect equal or superior."
    char_type: CharacterType = CharacterType.C
    gacha_rarity = 0
    damage_type: DamageTypeBase = field(
        default_factory=lambda: load_damage_type(choice(ALL_DAMAGE_TYPES))
    )
    passives: list[str] = field(default_factory=lambda: ["mimic_player_copy"])
    ui_portrait_pool: ClassVar[str] = "player_mirror"
    ui_non_selectable: ClassVar[bool] = True
