"""Character plugin: Ryne."""
from dataclasses import dataclass, field
from plugins.characters._base import IdleCharacter


@dataclass
class Ryne(IdleCharacter):
    """Character: Ryne."""
    
    id: str = "ryne"
    name: str = "Ryne"
    short_lore: str = """An Oracle of Light who leads restoration missions with calm resolve, channeling light through twin blades with agile precision."""
    full_lore: str = """Ryne Waters is a 6★ Oracle of Light who chose her own name and future after escaping Eulmore. She now leads restoration missions across the Empty with calm resolve, balancing empathy with a scout's edge learned alongside her mentor Thancred. Her partnership with Luna Midori keeps both grounded—Luna tempers Ryne's habit of carrying every burden alone while Ryne helps Luna open up to the communities they protect. In battle she channels light through twin blades or a borrowed gunblade, moving with agile precision to cleanse aetheric storms and shield her friends."""
    char_type: str = "B"
    gacha_rarity: int = 6
    damage_type: str = "load_damage_type"
    passives: list = field(default_factory=lambda: ["ryne_oracle_of_balance"])
    special_abilities: list = field(default_factory=lambda: [])
    ui: dict = field(default_factory=lambda: {"portrait": "/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/Experimentation/Python-idle-game/idle_game/assets/characters/ryne"})
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
