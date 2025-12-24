"""Character plugin: Kboshi."""
from dataclasses import dataclass, field
from plugins.characters._base import IdleCharacter


@dataclass
class Kboshi(IdleCharacter):
    """Character: Kboshi."""
    
    id: str = "kboshi"
    name: str = "Kboshi"
    short_lore: str = """A master of dark energy who channels void forces through cyclical attacks, tearing at reality with perpetual loops of destruction."""
    full_lore: str = """A master of dark energy whose deep understanding of shadow and void allows him to harness forces that most fear to touch. His flux cycle abilities create devastating cyclical attacks by channeling dark energy through perpetual loops of creation and destruction. Kboshi manipulates the fundamental forces of entropy, drawing power from the spaces between light and using that darkness to fuel increasingly powerful dark magic. His energy manipulation doesn't just deal damage—it tears at the fabric of reality itself, creating vortexes of pure void that consume everything in their path before cycling back to fuel his next devastating assault."""
    char_type: str = "A"
    gacha_rarity: int = 5
    damage_type: str = "load_damage_type"
    passives: list = field(default_factory=lambda: ["kboshi_flux_cycle"])
    special_abilities: list = field(default_factory=lambda: [])
    ui: dict = field(default_factory=lambda: {"portrait": "/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/Experimentation/Python-idle-game/idle_game/assets/characters/kboshi"})
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
