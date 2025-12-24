"""Character plugin: LadyStorm."""
from dataclasses import dataclass
from dataclasses import field

from plugins.characters._base import IdleCharacter


@dataclass
class LadyStorm(IdleCharacter):
    """Character: LadyStorm."""

    id: str = "lady_storm"
    name: str = "LadyStorm"
    short_lore: str = """An aasimar tempest caller who bends storms into weapons, capable of gentle tailwinds or catastrophic derechos."""
    full_lore: str = """Lady Storm is a 6★ aasimar tempest caller whose light green-and-yellow hair flickers like bottled lightning. She keeps a cluttered war room and laughs through the chaos, riding manic focus to bend slipstreams into battering rams. Villages still whisper about the night she flattened whole townships by threading tornadic downdrafts with chain lightning—one moment she is a gentle tailwind, the next a cataclysmic derecho that scours the map clean."""
    char_type: str = "B"
    gacha_rarity: int = 6
    damage_type: str = "load_damage_type"
    passives: list = field(default_factory=lambda: ["lady_storm_supercell"])
    special_abilities: list = field(default_factory=lambda: [])
    ui: dict = field(default_factory=lambda: {"portrait": "/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/Experimentation/Python-idle-game/idle_game/assets/characters/lady_storm"})
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
