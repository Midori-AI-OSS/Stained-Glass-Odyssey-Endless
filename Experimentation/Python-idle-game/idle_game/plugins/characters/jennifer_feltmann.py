"""Character plugin: Jennifer Feltmann."""
from dataclasses import dataclass
from dataclasses import field

from plugins.characters._base import IdleCharacter


@dataclass
class JenniferFeltmann(IdleCharacter):
    """Character: Jennifer Feltmann."""

    id: str = "jennifer_feltmann"
    name: str = "Jennifer Feltmann"
    short_lore: str = """A veteran programming and robotics teacher who channels twenty years of classroom management into debilitating 'bad student' debuffs that bring chaos to a grinding halt."""
    full_lore: str = """Jennifer Feltmann is a veteran high school programming and robotics teacher who has dedicated over twenty years to shaping young minds in technology. Her approach to teaching blends patient guidance with firm expectations—she believes every student can succeed with the right encouragement and structure. Beyond the classroom, she's the kind of mentor who remembers which student struggles with recursion and which one lights up at hardware projects. Her 'bad student' abilities in combat are less about cruelty and more about the exhausting reality of managing a classroom full of teenagers who forgot their assignments again—manifesting as debilitating debuffs that grind enemies to a halt like a lecture on proper variable naming conventions."""
    char_type: str = "B"
    gacha_rarity: int = 5
    damage_type: str = "Dark"
    passives: list = field(default_factory=lambda: ["bad_student"])
    special_abilities: list = field(default_factory=lambda: [])
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
