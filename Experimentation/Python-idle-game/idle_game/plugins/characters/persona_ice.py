"""Character plugin: PersonaIce."""
from dataclasses import dataclass, field
from plugins.characters._base import IdleCharacter


@dataclass
class PersonaIce(IdleCharacter):
    """Character: PersonaIce."""
    
    id: str = "persona_ice"
    name: str = "PersonaIce"
    short_lore: str = """A disciplined cryokinetic tank who shields his sisters with protective frost that hardens against blows and heals allies."""
    full_lore: str = """A disciplined cryokinetic tank who keeps his real name hidden behind the PersonaIce moniker. He is most comfortable blanketing a battlefield in calming frost, projecting the chill aura that never leaves his ice-blue hair. PersonaIce fights to shield his sisters—Lady of Fire and Lady Fire and Ice—layering protective cold around them before reshaping it into restorative mist. Though still barely past his twentieth winter, the human wanderer has mastered a meditative cycle of ice that hardens against enemy blows and then thaws into healing for the party."""
    char_type: str = "A"
    gacha_rarity: int = 5
    damage_type: str = "Ice"
    passives: list = field(default_factory=lambda: ["persona_ice_cryo_cycle"])
    special_abilities: list = field(default_factory=lambda: [])
    ui: dict = field(default_factory=lambda: {"portrait": "/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/Experimentation/Python-idle-game/idle_game/assets/characters/persona_ice.png"})
    base_stats: dict = field(default_factory=lambda: {
        "max_hp": 1650,
        "atk": 100,
        "defense": 210,
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
