from dataclasses import dataclass
from dataclasses import field

from autofighter.character import CharacterType
from plugins.damage_types._base import DamageTypeBase
from plugins.damage_types.wind import Wind
from plugins.players._base import PlayerBase


@dataclass
class LadyWind(PlayerBase):
    id = "lady_wind"
    name = "LadyWind"
    about = (
        "Persona Wind - Lady Wind is the twin sister of Lady Lightning, a"
        " female Aasimar whose ageless features hover somewhere between twenty"
        " and thirty-two. She lives in a perpetually messy aeromancy studio"
        " where scattered schematics and wind-torn journals reveal the manic"
        " focus that keeps her experiments spinning."
        " She stalks the halls in a green, off-shoulder strapless dress, her"
        " dark green crystal hair cropped with restless bangs above luminous"
        " green eyes. When she walks, a shimmering gale wraps around her,"
        " flecked with upset motes of blood that never seem to touch the"
        " floor, and every step rings with the hum of the storm she keeps"
        " caged inside her ribs. The lash of that captive wind leaves hairline"
        " cuts across her arms and shoulders—she is always bleeding crystal"
        " green blood due to the wind around her, though the droplets spiral"
        " in place instead of falling."
        " Despite the chaos, she guards her allies with razor focus—layering"
        " wind wards, calming Lady Lightning's tempests, and whispering flight"
        " equations to anyone brave enough to listen."
    )
    char_type: CharacterType = CharacterType.B
    gacha_rarity = 5
    damage_type: DamageTypeBase = field(default_factory=Wind)
    passives: list[str] = field(default_factory=lambda: ["lady_wind_tempest_guard"])
