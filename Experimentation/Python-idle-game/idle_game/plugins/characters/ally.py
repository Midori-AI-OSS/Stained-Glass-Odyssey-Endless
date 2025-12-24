"""Character plugin: Ally."""
from dataclasses import dataclass, field
from plugins.characters._base import IdleCharacter


@dataclass
class Ally(IdleCharacter):
    """Character: Ally."""
    
    id: str = "ally"
    name: str = "Ally"
    short_lore: str = """A versatile support fighter who reads the battlefield like a chess master, overloading enemy systems with strategic elemental manipulation."""
    full_lore: str = """A versatile support fighter whose tactical brilliance shines through her overload capabilities, systematically dismantling enemy defenses through strategic elemental manipulation. Known for her uncanny adaptability, Ally reads the battlefield like a chess master, identifying weak points in enemy formations and exploiting them with perfectly timed elemental strikes. Her mastery spans all damage types, allowing her to adapt her combat style to counter any opponent. In combat, she excels at overloading enemy systems—disrupting their magical circuits, overwhelming their defenses, and creating cascade failures that turn their own power against them."""
    char_type: str = "B"
    gacha_rarity: int = 5
    damage_type: str = "load_damage_type"
    passives: list = field(default_factory=lambda: ["ally_overload"])
    special_abilities: list = field(default_factory=lambda: ["special.ally.overload_cascade"])
    ui: dict = field(default_factory=lambda: {"portrait": "/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/Experimentation/Python-idle-game/idle_game/assets/characters/ally.png"})
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
