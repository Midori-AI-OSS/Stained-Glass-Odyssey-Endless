from dataclasses import dataclass
from dataclasses import field

from autofighter.character import CharacterType
from plugins.characters._base import PlayerBase
from plugins.damage_types._base import DamageTypeBase
from plugins.damage_types.ice import Ice


@dataclass
class PersonaIce(PlayerBase):
    id = "persona_ice"
    name = "PersonaIce"
    about = (
        "A disciplined cryokinetic tank who keeps his real name hidden behind the Persona"
        "Ice moniker. He is most comfortable blanketing a battlefield in calming frost, "
        "projecting the chill aura that never leaves his ice-blue hair. PersonaIce fights "
        "to shield his sisters—Lady of Fire and Lady Fire and Ice—layering protective cold "
        "around them before reshaping it into restorative mist. Though still barely past "
        "his twentieth winter, the human wanderer has mastered a meditative cycle of ice "
        "that hardens against enemy blows and then thaws into healing for the party."
    )
    char_type: CharacterType = CharacterType.A
    gacha_rarity = 5
    damage_type: DamageTypeBase = field(default_factory=Ice)
    passives: list[str] = field(default_factory=lambda: ["persona_ice_cryo_cycle"])

    def __post_init__(self) -> None:
        super().__post_init__()
        self.set_base_stat("mitigation", 4.0)
        self.set_base_stat("defense", 210)
        self.set_base_stat("max_hp", 1650)
        self.base_aggro = 2.35
        self.hp = self.max_hp
