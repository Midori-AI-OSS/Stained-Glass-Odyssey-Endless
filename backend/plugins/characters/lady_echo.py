from dataclasses import dataclass
from dataclasses import field
from typing import ClassVar

from autofighter.character import CharacterType
from plugins.characters._base import PlayerBase
from plugins.damage_types._base import DamageTypeBase
from plugins.damage_types.lightning import Lightning


@dataclass
class LadyEcho(PlayerBase):
    id = "lady_echo"
    name = "LadyEcho"
    about = "Echo, a 22-year-old Aasimar inventor with distinctive light yellow hair and a brilliant mind shaped by Asperger's Syndrome. Her high intelligence manifests in an obsessive passion for building and creating, constantly tinkering with devices that blur the line between magic and technology. In combat, her resonant static abilities create powerful lightning echoes that reverberate across the battlefield—but every use of her powers comes with a cost. Minor abilities de-age her by 12 hours, while major powers can steal up to a year from her apparent age. This limitation drives her inventive nature as she seeks to build devices that might mitigate or reverse the de-aging effect. Despite social challenges from her neurodiversity, her heroic drive compels her to help others, even when the price is measured in lost time."
    char_type: CharacterType = CharacterType.B
    gacha_rarity = 5
    damage_type: DamageTypeBase = field(default_factory=Lightning)
    passives: list[str] = field(default_factory=lambda: ["lady_echo_resonant_static"])
    ui_portrait_pool: ClassVar[str] = "player_gallery"

