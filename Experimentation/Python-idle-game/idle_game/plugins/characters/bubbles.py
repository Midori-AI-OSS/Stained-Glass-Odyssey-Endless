"""Character plugin: Bubbles."""
from dataclasses import dataclass, field
from plugins.characters._base import IdleCharacter


@dataclass
class Bubbles(IdleCharacter):
    """Character: Bubbles."""
    
    id: str = "bubbles"
    name: str = "Bubbles"
    short_lore: str = """An enthusiastic aquatic fighter who creates cascading bubble explosions, turning playful attacks into devastating chain reactions."""
    full_lore: str = """An enthusiastic aquatic fighter whose bubbly personality masks a devastating combat style built around explosive chain reactions. His bubble burst abilities create cascading detonations that spread across the battlefield like underwater fireworks—each burst triggering additional explosions in a symphony of aquatic destruction. With boundless energy and an infectious optimism, Bubbles approaches every battle like a game, but his seemingly playful attacks pack tremendous force. His mastery of pressure dynamics allows him to create bubble formations that can both shield allies and devastate enemies when they inevitably pop."""
    char_type: str = "A"
    gacha_rarity: int = 5
    damage_type: str = "load_damage_type"
    passives: list = field(default_factory=lambda: ["bubbles_bubble_burst"])
    special_abilities: list = field(default_factory=lambda: [])
    ui: dict = field(default_factory=lambda: {"portrait": "/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/Experimentation/Python-idle-game/idle_game/assets/characters/bubbles.png"})
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
