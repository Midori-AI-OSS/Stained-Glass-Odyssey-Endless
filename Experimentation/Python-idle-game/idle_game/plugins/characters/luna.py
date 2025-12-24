"""Character plugin: Luna."""
from dataclasses import dataclass, field
from plugins.characters._base import IdleCharacter


@dataclass
class Luna(IdleCharacter):
    """Character: Luna."""
    
    id: str = "luna"
    name: str = "Luna"
    short_lore: str = """A precise starlit scholar who fights with moonlight magic and calculated blade work, controlling the battlefield like a clockmaker in a storm."""
    full_lore: str = """Luna Midori fights like a stargazer who mapped the constellations of violence—quiet, exact, always a beat ahead. Her thin astral halo brightens as she sketches unseen wards; the Vessel of the Twin Veils keeps station at her shoulder, flaring to tip arrows off-line. She opens by controlling the field: silvery pressure that anchors feet, a hush that snuffs a spell mid-syllable, a ripple that leaves an after-image where she stood. When steel is required, the Glimmersteel rapier writes quick, grammatical cuts, the golden quarterstaff sets the tempo and distance, and the Bladeshift dagger ends what hesitation begins. She moves light and economical—cloak skimming stone, angles over brute force—talking just enough to knock an enemy off rhythm. Her magic is moon-cold and precise: starlight darts, gravity tugs, the soft collapse of air before a controlled blast—never wasteful, always aimed at the lever that topples the fight. She isn't a brawler; she's a clockmaker in a storm, turning the right gear until the whole field ticks her way."""
    char_type: str = "B"
    gacha_rarity: int = 0
    damage_type: str = "load_damage_type"
    passives: list = field(default_factory=lambda: ["luna_lunar_reservoir"])
    special_abilities: list = field(default_factory=lambda: [])
    ui: dict = field(default_factory=lambda: {"portrait": "/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/Experimentation/Python-idle-game/idle_game/assets/characters/luna"})
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
