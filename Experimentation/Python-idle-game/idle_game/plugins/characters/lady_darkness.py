"""Character plugin: LadyDarkness."""
from dataclasses import dataclass, field
from plugins.characters._base import IdleCharacter


@dataclass
class LadyDarkness(IdleCharacter):
    """Character: LadyDarkness."""
    
    id: str = "lady_darkness"
    name: str = "LadyDarkness"
    short_lore: str = """An elegant Aasimar sorceress who commands shadows through an eclipsing veil, creating inescapable shrouds of despair."""
    full_lore: str = """A 23-year-old Aasimar whose affinity for the Dark domain stained her hair to mirror-polished black, salted with white sparks like stars trapped in obsidian—an inversion of her sister Lady Light’s tresses. She is composed, aristocratic, and ruthlessly empathetic: the sibling who handles negotiations, recites lineage prayers from memory, and keeps score of every slight dealt to their found family. The eclipsing veil she wields is a social tool as much as a weapon; she folds people into its quiet when they need solace and crushes enemies beneath it when they refuse mercy. Her pepper-colored eyes seem to absorb light itself, and her entropy magic dismantles threats with the precision of someone who plans three moves ahead. Where her sister affirms existence, Lady Darkness curates what deserves to remain—an elegant arbiter of shadow who moves between worlds with choreographed grace."""
    char_type: str = "B"
    gacha_rarity: int = 5
    damage_type: str = "Dark"
    passives: list = field(default_factory=lambda: ["lady_darkness_eclipsing_veil"])
    special_abilities: list = field(default_factory=lambda: [])
    ui: dict = field(default_factory=lambda: {"portrait": "/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/Experimentation/Python-idle-game/idle_game/assets/characters/lady_darkness.png"})
    base_stats: dict = field(default_factory=lambda: {
        "max_hp": 1000,
        "atk": 100,
        "defense": 50,
        "mitigation": 1.0,
        "base_aggro": 1.0,
        "crit_rate": 0.05,
        "crit_damage": 2.0,
        "effect_hit_rate": 1.0,
        "regain": 0,
        "dodge_odds": 0.0,
        "effect_resistance": 0.0,
        "vitality": 1.0,
    })
