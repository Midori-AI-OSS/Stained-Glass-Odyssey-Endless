"""Character plugin: Graygray."""
from dataclasses import dataclass
from dataclasses import field

from plugins.characters._base import IdleCharacter


@dataclass
class Graygray(IdleCharacter):
    """Character: Graygray."""

    id: str = "graygray"
    name: str = "Graygray"
    short_lore: str = """A tactical mastermind who conducts battles like a symphony, converting enemy attacks into perfectly timed counters."""
    full_lore: str = """A tactical mastermind whose counter maestro abilities transform every enemy attack into a lesson in superior combat technique. Graygray doesn't just defend—she conducts battles like a symphony, turning opponent aggression into the very notes of their defeat. Her strategic brilliance lies in reading attack patterns and responding with perfectly timed counters that not only negate damage but convert that energy into devastating retaliations. Each strike against her becomes a teaching moment, as she demonstrates how true mastery lies not in overwhelming force, but in precise timing and flawless technique."""
    char_type: str = "B"
    gacha_rarity: int = 5
    damage_type: str = "load_damage_type"
    passives: list = field(default_factory=lambda: ["graygray_counter_maestro"])
    special_abilities: list = field(default_factory=lambda: ["special.graygray.counter_opus"])
    ui: dict = field(default_factory=lambda: {"portrait": "/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/Experimentation/Python-idle-game/idle_game/assets/characters/graygray.png"})
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
