from dataclasses import dataclass
from dataclasses import field

from autofighter.character import CharacterType
from plugins.characters._base import PlayerBase
from plugins.damage_types._base import DamageTypeBase
from plugins.damage_types.light import Light


@dataclass
class Carly(PlayerBase):
    id = "carly"
    name = "Carly"
    about = "A sim human model whose core programming revolves around protecting others above all else. Her protective instincts run deeper than mere code—they define her very essence. In combat, her guardian's aegis manifests as brilliant light barriers that redirect her offensive potential into impenetrable defense. She fights not to win, but to ensure everyone gets home safely. Every strike she deflects, every ally she shields, reinforces her fundamental drive: people's safety comes first, always. Her light magic doesn't just heal wounds—it mends the very concept of harm itself."
    char_type: CharacterType = CharacterType.B
    gacha_rarity = 5
    damage_type: DamageTypeBase = field(default_factory=Light)
    stat_gain_map: dict[str, str] = field(
        default_factory=lambda: {"atk": "defense"}
    )
    passives: list[str] = field(default_factory=lambda: ["carly_guardians_aegis"])
    # UI hint: show numeric actions indicator
    actions_display: str = "number"

    def __post_init__(self) -> None:
        super().__post_init__()
        self.damage_reduction_passes = 2
        self.set_base_stat("mitigation", 4.0)
        self.set_base_stat("defense", 220)
        self.set_base_stat("max_hp", 1600)
        self.base_aggro = 2.35
        self.hp = self.max_hp
