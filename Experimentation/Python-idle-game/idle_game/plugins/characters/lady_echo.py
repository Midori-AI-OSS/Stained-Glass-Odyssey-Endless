"""Character plugin: LadyEcho."""
from dataclasses import dataclass, field
from plugins.characters._base import IdleCharacter


@dataclass
class LadyEcho(IdleCharacter):
    """Character: LadyEcho."""
    
    id: str = "lady_echo"
    name: str = "LadyEcho"
    short_lore: str = """A brilliant Aasimar inventor whose lightning echoes reverberate across the battlefield, each use costing her time from her age."""
    full_lore: str = """Echo, a 22-year-old Aasimar inventor with distinctive light yellow hair and a brilliant mind shaped by Asperger's Syndrome. Her high intelligence manifests in an obsessive passion for building and creating, constantly tinkering with devices that blur the line between magic and technology. In combat, her resonant static abilities create powerful lightning echoes that reverberate across the battlefield—but every use of her powers comes with a cost. Minor abilities de-age her by 12 hours, while major powers can steal up to a year from her apparent age. This limitation drives her inventive nature as she seeks to build devices that might mitigate or reverse the de-aging effect. Despite social challenges from her neurodiversity, her heroic drive compels her to help others, even when the price is measured in lost time."""
    char_type: str = "B"
    gacha_rarity: int = 5
    damage_type: str = "Lightning"
    passives: list = field(default_factory=lambda: ["lady_echo_resonant_static"])
    special_abilities: list = field(default_factory=lambda: [])
    ui: dict = field(default_factory=lambda: {"portrait_pool": "player_gallery", "portrait": "/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/Experimentation/Python-idle-game/idle_game/assets/characters/lady_echo"})
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
