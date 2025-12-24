"""Character plugin: Mezzy."""
from dataclasses import dataclass
from dataclasses import field

from plugins.characters._base import IdleCharacter


@dataclass
class Mezzy(IdleCharacter):
    """Character: Mezzy."""

    id: str = "mezzy"
    name: str = "Mezzy"
    short_lore: str = """A voracious defender who devours enemy attacks and converts them into power, growing stronger with every blow."""
    full_lore: str = """A voracious defender whose gluttonous bulwark represents the ultimate expression of 'what doesn't kill you makes you stronger.' Mezzy literally devours enemy attacks, her unique physiology converting incoming damage into raw power that fuels her own abilities. The more her opponents throw at her, the stronger she becomes—creating a terrifying feedback loop where every assault just makes her hungrier for more. Her combat style revolves around tanking massive amounts of damage while growing exponentially more dangerous, turning what should be weakening blows into a feast that only strengthens her resolve and fighting capability."""
    char_type: str = "B"
    gacha_rarity: int = 5
    damage_type: str = "load_damage_type"
    passives: list = field(default_factory=lambda: ["mezzy_gluttonous_bulwark"])
    special_abilities: list = field(default_factory=lambda: [])
    ui: dict = field(default_factory=lambda: {"portrait": "/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/Experimentation/Python-idle-game/idle_game/assets/characters/mezzy.png"})
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
