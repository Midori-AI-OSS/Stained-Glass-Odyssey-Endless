from dataclasses import dataclass
from dataclasses import field

from autofighter.character import CharacterType
from plugins.damage_types._base import DamageTypeBase
from plugins.damage_types.fire import Fire
from plugins.characters._base import PlayerBase


@dataclass
class LadyOfFire(PlayerBase):
    id = "lady_of_fire"
    name = "LadyOfFire"
    about = "A fierce pyromancer appearing to be 18-20 years old, whose dark red hair flows like liquid flame and whose very presence exudes overwhelming warmth. Living with Dissociative Schizophrenia, she channels her condition into her fire magic, allowing different aspects of her psyche to fuel increasingly intense infernal momentum. Each enemy defeated feeds her inner flame, building heat waves that grow stronger with every victory. Her red eyes burn with hot intensity, and her fire magic seems to pulse with the rhythm of her fractured consciousness, creating unpredictable but devastatingly effective pyroclastic attacks."
    gacha_rarity = 5
    char_type: CharacterType = CharacterType.B
    damage_type: DamageTypeBase = field(default_factory=Fire)
    passives: list[str] = field(default_factory=lambda: ["lady_of_fire_infernal_momentum"])
