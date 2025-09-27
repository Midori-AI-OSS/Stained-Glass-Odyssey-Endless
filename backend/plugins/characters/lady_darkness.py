from dataclasses import dataclass
from dataclasses import field

from autofighter.character import CharacterType
from plugins.damage_types._base import DamageTypeBase
from plugins.damage_types.dark import Dark
from plugins.characters._base import PlayerBase


@dataclass
class LadyDarkness(PlayerBase):
    id = "lady_darkness"
    name = "LadyDarkness"
    about = "A 23-year-old Aasimar who embodies the elegant darkness of the void, her jet black hair and preference for dark colors making her a striking figure on any battlefield. Her mysterious sorceress nature commands shadows through her eclipsing veil, which doesn't just darken the field—it creates an inescapable shroud of despair that weighs on enemies' souls. Her pepper-colored eyes seem to absorb light itself, and her dark magic manifests as controlled entropy that systematically dismantles her opponents' will to fight. She moves with the grace of shadows given form, her eclipsing veil making her seem to phase between darkness and reality."
    char_type: CharacterType = CharacterType.B
    gacha_rarity = 5
    damage_type: DamageTypeBase = field(default_factory=Dark)
    passives: list[str] = field(default_factory=lambda: ["lady_darkness_eclipsing_veil"])
