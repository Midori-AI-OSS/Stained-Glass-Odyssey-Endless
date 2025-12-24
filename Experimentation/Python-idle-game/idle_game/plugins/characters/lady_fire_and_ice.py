"""Character plugin: LadyFireAndIce."""
from dataclasses import dataclass, field
from plugins.characters._base import IdleCharacter


@dataclass
class LadyFireAndIce(IdleCharacter):
    """Character: LadyFireAndIce."""
    
    id: str = "lady_fire_and_ice"
    name: str = "LadyFireAndIce"
    short_lore: str = """A dual-natured elemental master who switches between volcanic fury and arctic precision, creating devastating thermal shocks."""
    full_lore: str = """A legendary 6★ elemental master appearing to be 18-20 years old, whose reddish-blue hair reflects her dual nature. Living with Dissociative Schizophrenia, she experiences herself as two distinct elemental personas that work in perfect, devastating harmony. Her fire alignment runs so hot that she sleeps unclothed to manage the constant heat radiating from her body. In combat, her duality engine allows her to wield both fire and ice through seamless persona switches—one moment erupting with volcanic fury, the next freezing enemies with arctic precision. The opposing forces create devastating thermal shocks that few opponents can withstand."""
    char_type: str = "B"
    gacha_rarity: int = 6
    damage_type: str = "load_damage_type"
    passives: list = field(default_factory=lambda: ["lady_fire_and_ice_duality_engine"])
    special_abilities: list = field(default_factory=lambda: [])
    ui: dict = field(default_factory=lambda: {"portrait": "/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/Experimentation/Python-idle-game/idle_game/assets/characters/lady_fire_and_ice.png"})
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
