from dataclasses import dataclass
from dataclasses import field

from autofighter.character import CharacterType
from plugins.characters._base import PlayerBase
from plugins.damage_types import load_damage_type
from plugins.damage_types._base import DamageTypeBase


@dataclass
class Casno(PlayerBase):
    """Fire-aligned gacha recruit who thrives on planned downtime."""

    id = "casno"
    name = "Casno"
    char_type: CharacterType = CharacterType.A
    gacha_rarity = 5
    damage_type: DamageTypeBase = field(default_factory=lambda: load_damage_type("Fire"))
    passives: list[str] = field(default_factory=lambda: ["casno_phoenix_respite"])
    about: str = (
        "A stoic veteran pyrokinetic who has learned to weaponize recovery. "
        "Casno tallies Relaxed stacks with every five attacks; once the gauge "
        "overflows, he skips his next strike to breathe, cashing in five stacks "
        "for a self-heal and 15% base-stat boons per stack before erupting back into combat."
    )
    voice_gender = "male"


__all__ = ["Casno"]
