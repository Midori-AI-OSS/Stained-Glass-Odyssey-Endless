"""Character plugin: PersonaLightAndDark."""
from dataclasses import dataclass
from dataclasses import field

from plugins.characters._base import IdleCharacter


@dataclass
class PersonaLightAndDark(IdleCharacter):
    """Character: PersonaLightAndDark."""

    id: str = "persona_light_and_dark"
    name: str = "PersonaLightAndDark"
    short_lore: str = """A guardian brother who trades between light and shadow, drawing enemy focus to protect his sisters and allies."""
    full_lore: str = """A 6★ guardian and brother to Lady Light and Lady Darkness, Persona Light and Dark fights to keep his sisters safe. He speaks only the radiant glyphs of the Light tongue, letting sweeping gestures and twin halos translate his intent. By trading between the family's luminous ward and shadow bastion, he drags enemy focus onto himself while sheltering the people he protects."""
    char_type: str = "A"
    gacha_rarity: int = 6
    damage_type: str = "load_damage_type"
    passives: list = field(default_factory=lambda: ["persona_light_and_dark_duality"])
    special_abilities: list = field(default_factory=lambda: [])
    ui: dict = field(default_factory=lambda: {"portrait": "/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/Experimentation/Python-idle-game/idle_game/assets/characters/persona_light_and_dark.png"})
    base_stats: dict = field(default_factory=lambda: {
        "max_hp": 1700,
        "atk": 100,
        "defense": 240,
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
