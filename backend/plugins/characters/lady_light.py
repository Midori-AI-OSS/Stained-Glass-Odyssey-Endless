from dataclasses import dataclass
from dataclasses import field

from autofighter.character import CharacterType
from plugins.damage_types._base import DamageTypeBase
from plugins.damage_types.light import Light
from plugins.characters._base import PlayerBase


@dataclass
class LadyLight(PlayerBase):
    id = "lady_light"
    name = "LadyLight"
    about = "A 23-year-old Aasimar whose once-pure white hair has transformed to purple, reflecting the changes wrought by her condition. Living with Cotard's Syndrome, she struggles with the belief that parts of her body don't exist or are dying—unable to use her left arm or right eye, which has begun to appear blind from disuse. Despite these severe limitations, she fights with unwavering determination, her radiant aegis compensating for her physical constraints by creating protective barriers that shield allies from all harm. She rooms with Cassy and undergoes physical therapy every six hours, but her greatest strength comes from her love of companionship and conversation with her fellow fighters. Her light magic doesn't just protect—it affirms existence itself against the void she perceives within."
    char_type: CharacterType = CharacterType.B
    gacha_rarity = 5
    damage_type: DamageTypeBase = field(default_factory=Light)
    passives: list[str] = field(default_factory=lambda: ["lady_light_radiant_aegis"])
