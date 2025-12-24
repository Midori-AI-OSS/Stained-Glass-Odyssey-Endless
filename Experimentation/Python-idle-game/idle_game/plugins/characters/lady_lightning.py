"""Character plugin: LadyLightning."""
from dataclasses import dataclass, field
from plugins.characters._base import IdleCharacter


@dataclass
class LadyLightning(IdleCharacter):
    """Character: LadyLightning."""
    
    id: str = "lady_lightning"
    name: str = "LadyLightning"
    short_lore: str = """Lady Wind's storm-tossed twin who escaped a lab and now channels lightning with manic intensity, unable to distinguish guidance from delusion."""
    full_lore: str = """An aasimar who answers to Electra—the storm-tossed twin of Lady Wind. Though she looks about thirty, her sunburst hair is permanently overcharged and her bright yellow eyes never stop darting. Electra broke out of the lab that laced her nerves with conductive implants, and the ordeal left her with disorganized thoughts, paranoia about whoever was pulling the switches, and manic surges that collapse into exhaustion. She insists she can hear every current humming around her, cobbling together unstable inventions or weaponizing the sparks when cornered. Even while certain the authorities are still hunting her, she fights beside the few people who believe her, channeling lightning like a prophet who cannot tell divine guidance from delusion."""
    char_type: str = "B"
    gacha_rarity: int = 5
    damage_type: str = "Lightning"
    passives: list = field(default_factory=lambda: ["lady_lightning_stormsurge"])
    special_abilities: list = field(default_factory=lambda: [])
    ui: dict = field(default_factory=lambda: {"portrait": "/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/Experimentation/Python-idle-game/idle_game/assets/characters/lady_lightning.png"})
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
