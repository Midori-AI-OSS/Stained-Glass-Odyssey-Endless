from dataclasses import dataclass
from dataclasses import field

from autofighter.character import CharacterType
from plugins.characters._base import PlayerBase
from plugins.damage_types._base import DamageTypeBase
from plugins.damage_types.lightning import Lightning


@dataclass
class LadyLightning(PlayerBase):
    id = "lady_lightning"
    name = "LadyLightning"
    about = (
        "An aasimar who answers to Electra—the storm-tossed twin of Lady Wind. "
        "Though she looks about thirty, her sunburst hair is permanently "
        "overcharged and her bright yellow eyes never stop darting. Electra broke "
        "out of the lab that laced her nerves with conductive implants, and the "
        "ordeal left her with disorganized thoughts, paranoia about whoever was "
        "pulling the switches, and manic surges that collapse into exhaustion. She "
        "insists she can hear every current humming around her, cobbling together "
        "unstable inventions or weaponizing the sparks when cornered. Even while "
        "certain the authorities are still hunting her, she fights beside the few "
        "people who believe her, channeling lightning like a prophet who cannot "
        "tell divine guidance from delusion."
    )
    char_type: CharacterType = CharacterType.B
    gacha_rarity = 5
    damage_type: DamageTypeBase = field(default_factory=Lightning)
    passives: list[str] = field(default_factory=lambda: ["lady_lightning_stormsurge"])
