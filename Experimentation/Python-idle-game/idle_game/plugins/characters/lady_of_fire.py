"""Character plugin: LadyOfFire."""
from dataclasses import dataclass
from dataclasses import field

from plugins.characters._base import IdleCharacter


@dataclass
class LadyOfFire(IdleCharacter):
    """Character: LadyOfFire."""

    id: str = "lady_of_fire"
    name: str = "LadyOfFire"
    short_lore: str = """A fierce pyromancer who channels her fractured consciousness into devastating fire magic, building infernal momentum with each victory."""
    full_lore: str = """A fierce pyromancer appearing to be 18-20 years old, whose dark red hair flows like liquid flame and whose very presence exudes overwhelming warmth. Living with Dissociative Schizophrenia, she channels her condition into her fire magic, allowing different aspects of her psyche to fuel increasingly intense infernal momentum. Each enemy defeated feeds her inner flame, building heat waves that grow stronger with every victory. Her red eyes burn with hot intensity, and her fire magic seems to pulse with the rhythm of her fractured consciousness, creating unpredictable but devastatingly effective pyroclastic attacks."""
    char_type: str = "B"
    gacha_rarity: int = 5
    damage_type: str = "Fire"
    passives: list = field(default_factory=lambda: ["lady_of_fire_infernal_momentum"])
    special_abilities: list = field(default_factory=lambda: [])
    ui: dict = field(default_factory=lambda: {"portrait": "/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/Experimentation/Python-idle-game/idle_game/assets/characters/lady_of_fire.png"})
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
