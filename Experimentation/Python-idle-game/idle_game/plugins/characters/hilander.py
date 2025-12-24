"""Character plugin: Hilander."""
from dataclasses import dataclass, field
from plugins.characters._base import IdleCharacter


@dataclass
class Hilander(IdleCharacter):
    """Character: Hilander."""
    
    id: str = "hilander"
    name: str = "Hilander"
    short_lore: str = """A passionate brewmaster who treats combat like a brewing process, creating explosive combinations through critical ferment techniques."""
    full_lore: str = """A passionate brewmaster whose alchemical expertise extends far beyond tavern walls into the heat of battle. His critical ferment techniques create explosive combinations by treating combat like a complex brewing process—mixing elements, timing reactions, and achieving the perfect catalyst moment for devastating results. Hilander approaches each fight with the same methodical passion he brings to crafting the perfect ale, understanding that the right combination of pressure, timing, and elemental ingredients can create effects far greater than the sum of their parts. His battlefield brewery turns every engagement into an opportunity to perfect his most volatile recipes."""
    char_type: str = "A"
    gacha_rarity: int = 5
    damage_type: str = "load_damage_type"
    passives: list = field(default_factory=lambda: ["hilander_critical_ferment"])
    special_abilities: list = field(default_factory=lambda: [])
    ui: dict = field(default_factory=lambda: {"portrait": "/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/Experimentation/Python-idle-game/idle_game/assets/characters/hilander.png"})
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
