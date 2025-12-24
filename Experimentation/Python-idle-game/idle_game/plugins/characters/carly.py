"""Character plugin: Carly."""
from dataclasses import dataclass, field
from plugins.characters._base import IdleCharacter


@dataclass
class Carly(IdleCharacter):
    """Character: Carly."""
    
    id: str = "carly"
    name: str = "Carly"
    short_lore: str = """A sim human guardian whose core programming is protection, converting offensive power into brilliant light barriers that keep everyone safe."""
    full_lore: str = """A sim human model whose core programming revolves around protecting others above all else. Her protective instincts run deeper than mere code—they define her very essence. In combat, her guardian's aegis manifests as brilliant light barriers that redirect her offensive potential into impenetrable defense. She fights not to win, but to ensure everyone gets home safely. Every strike she deflects, every ally she shields, reinforces her fundamental drive: people's safety comes first, always. Her light magic doesn't just heal wounds—it mends the very concept of harm itself."""
    char_type: str = "B"
    gacha_rarity: int = 5
    damage_type: str = "Light"
    passives: list = field(default_factory=lambda: ["carly_guardians_aegis"])
    special_abilities: list = field(default_factory=lambda: ["special.carly.guardian_barrier"])
    ui: dict = field(default_factory=lambda: {"portrait": "/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/Experimentation/Python-idle-game/idle_game/assets/characters/carly.png"})
    base_stats: dict = field(default_factory=lambda: {
        "max_hp": 1600,
        "atk": 100,
        "defense": 220,
        "mitigation": 4.0,
        "base_aggro": 2.35,
        "crit_rate": 0.05,
        "crit_damage": 2.0,
        "effect_hit_rate": 1.0,
        "regain": 0,
        "dodge_odds": 0.0,
        "effect_resistance": 0.0,
        "vitality": 1.0,
    })
