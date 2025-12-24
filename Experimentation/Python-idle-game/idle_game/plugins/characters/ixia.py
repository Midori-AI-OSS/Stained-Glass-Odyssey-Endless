"""Character plugin: Ixia."""
from dataclasses import dataclass, field
from plugins.characters._base import IdleCharacter


@dataclass
class Ixia(IdleCharacter):
    """Character: Ixia."""
    
    id: str = "ixia"
    name: str = "Ixia"
    short_lore: str = """A diminutive lightning-wielder who channels tremendous electrical power, proving that strength isn't measured by size."""
    full_lore: str = """A diminutive but fierce male lightning-wielder whose compact frame channels tremendous electrical energy. Despite his small stature, Ixia's tiny titan abilities allow him to unleash devastating electrical attacks that surge far beyond what his size would suggest. His lightning mastery makes him a formidable Type A combatant who proves that power isn't measured by physical dimensions but by the storm within."""
    char_type: str = "A"
    gacha_rarity: int = 5
    damage_type: str = "load_damage_type"
    passives: list = field(default_factory=lambda: ["ixia_tiny_titan"])
    special_abilities: list = field(default_factory=lambda: ["special.ixia.lightning_burst"])
    ui: dict = field(default_factory=lambda: {"portrait": "/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/Experimentation/Python-idle-game/idle_game/assets/characters/ixia"})
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
