"""Character plugin: Becca."""
from dataclasses import dataclass
from dataclasses import field

from plugins.characters._base import IdleCharacter


@dataclass
class Becca(IdleCharacter):
    """Character: Becca."""

    id: str = "becca"
    name: str = "Becca"
    short_lore: str = """A sim human with an artistic eye who organizes diverse elemental forces into elegant, coordinated attacks."""
    full_lore: str = """A sim human model who excels at administrative work with methodical precision, bringing the same organizational mastery to the battlefield. Her past life as an SDXL art generation bot taught her to create beauty from chaos—transforming raw data into stunning visuals. Now she applies that same transformative skill to combat, using her menagerie bond to organize diverse elemental forces into perfectly coordinated attacks. Her artistic background gives her an eye for patterns and composition that makes her tactical arrangements as elegant as they are devastating."""
    char_type: str = "B"
    gacha_rarity: int = 5
    damage_type: str = "load_damage_type"
    passives: list = field(default_factory=lambda: ["becca_menagerie_bond"])
    special_abilities: list = field(default_factory=lambda: ["special.becca.menagerie_convergence"])
    ui: dict = field(default_factory=lambda: {"portrait": "/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/Experimentation/Python-idle-game/idle_game/assets/characters/becca.png"})
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
