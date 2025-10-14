from dataclasses import dataclass
from dataclasses import field

from autofighter.character import CharacterType
from plugins.characters._base import PlayerBase
from plugins.damage_types import load_damage_type
from plugins.damage_types._base import DamageTypeBase


@dataclass
class Ryne(PlayerBase):
    id = "ryne"
    name = "Ryne"
    about = (
        "Ryne Waters is a 6★ Oracle of Light who chose her own name and future after escaping"
        " Eulmore. She now leads restoration missions across the Empty with calm resolve,"
        " balancing empathy with a scout's edge learned alongside her mentor Thancred."
        " Her partnership with Luna Midori keeps both grounded—Luna tempers Ryne's habit of"
        " carrying every burden alone while Ryne helps Luna open up to the communities they"
        " protect. In battle she channels light through twin blades or a borrowed gunblade,"
        " moving with agile precision to cleanse aetheric storms and shield her friends."
    )
    char_type: CharacterType = CharacterType.B
    gacha_rarity = 6
    damage_type: DamageTypeBase = field(default_factory=lambda: load_damage_type("Light"))
    passives: list[str] = field(default_factory=lambda: ["ryne_oracle_of_balance"])
    actions_display: str = "number"
