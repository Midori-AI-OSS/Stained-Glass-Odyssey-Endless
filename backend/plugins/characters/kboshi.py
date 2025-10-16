from dataclasses import dataclass
from dataclasses import field

from autofighter.character import CharacterType
from plugins.characters._base import PlayerBase
from plugins.damage_types import load_damage_type
from plugins.damage_types._base import DamageTypeBase


@dataclass
class Kboshi(PlayerBase):
    id = "kboshi"
    name = "Kboshi"
    about = "A master of dark energy whose deep understanding of shadow and void allows him to harness forces that most fear to touch. His flux cycle abilities create devastating cyclical attacks by channeling dark energy through perpetual loops of creation and destruction. Kboshi manipulates the fundamental forces of entropy, drawing power from the spaces between light and using that darkness to fuel increasingly powerful dark magic. His energy manipulation doesn't just deal damage—it tears at the fabric of reality itself, creating vortexes of pure void that consume everything in their path before cycling back to fuel his next devastating assault."
    char_type: CharacterType = CharacterType.A
    gacha_rarity = 5
    damage_type: DamageTypeBase = field(
        default_factory=lambda: load_damage_type("Dark")
    )
    passives: list[str] = field(default_factory=lambda: ["kboshi_flux_cycle"])
