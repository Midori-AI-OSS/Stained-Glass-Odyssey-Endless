"""Character plugin: LadyLight."""
from dataclasses import dataclass
from dataclasses import field

from plugins.characters._base import IdleCharacter


@dataclass
class LadyLight(IdleCharacter):
    """Character: LadyLight."""

    id: str = "lady_light"
    name: str = "LadyLight"
    short_lore: str = """An Aasimar battling Cotard's Syndrome who creates protective light barriers to affirm existence against the void she perceives within."""
    full_lore: str = """A 23-year-old Aasimar whose soul aligned so purely with the Light domain that her hair bleached to lunar white threaded with black starlike flecks. Sister to Lady Darkness, she plays the role of steady hearth-fire: the soft-spoken guardian who remembers everyone’s schedules, writes encouragement notes, and volunteers for the final watch so others can sleep. Cotard's Syndrome still steals sensation from her left arm and blinds the right eye, but she refuses to let the illness define her. Therapy sessions every six hours keep her body moving, while radiant aegis drills keep her hope sharp. When she steps between an ally and danger, the gesture feels less like a spell and more like a promise—she will hold the line, believe in their existence, and lend them her light even when she doubts her own."""
    char_type: str = "B"
    gacha_rarity: int = 5
    damage_type: str = "Light"
    passives: list = field(default_factory=lambda: ["lady_light_radiant_aegis"])
    special_abilities: list = field(default_factory=lambda: [])
    ui: dict = field(default_factory=lambda: {"portrait": "/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/Experimentation/Python-idle-game/idle_game/assets/characters/lady_light.png"})
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
