from dataclasses import dataclass
from dataclasses import field
from random import choice

from autofighter.character import CharacterType
from plugins.characters._base import PlayerBase
from plugins.damage_types import load_damage_type
from plugins.damage_types._base import DamageTypeBase


@dataclass
class LadyStorm(PlayerBase):
    id = "lady_storm"
    name = "LadyStorm"
    about = (
        "Lady Storm is a 6★ aasimar tempest caller whose light green-and-yellow hair flickers"
        " like bottled lightning. She keeps a cluttered war room and laughs through the chaos,"
        " riding manic focus to bend slipstreams into battering rams. Villages still whisper"
        " about the night she flattened whole townships by threading tornadic downdrafts with"
        " chain lightning—one moment she is a gentle tailwind, the next a cataclysmic derecho"
        " that scours the map clean."
    )
    char_type: CharacterType = CharacterType.B
    gacha_rarity = 6
    damage_type: DamageTypeBase = field(
        default_factory=lambda: load_damage_type(choice(["Wind", "Lightning"]))
    )
    passives: list[str] = field(default_factory=lambda: ["lady_storm_supercell"])
