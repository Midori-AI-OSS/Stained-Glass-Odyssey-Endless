"""Character plugin: LadyWind."""
from dataclasses import dataclass
from dataclasses import field

from plugins.characters._base import IdleCharacter


@dataclass
class LadyWind(IdleCharacter):
    """Character: LadyWind."""

    id: str = "lady_wind"
    name: str = "LadyWind"
    short_lore: str = """Lady Lightning's twin sister, an Aasimar aeromancer cloaked in bleeding winds who guards allies with precision despite her chaotic experiments."""
    full_lore: str = """Persona Wind - Lady Wind is the twin sister of Lady Lightning, a female Aasimar whose ageless features hover somewhere between twenty and thirty-two. She lives in a perpetually messy aeromancy studio where scattered schematics and wind-torn journals reveal the manic focus that keeps her experiments spinning. She stalks the halls in a green, off-shoulder strapless dress, her dark green crystal hair cropped with restless bangs above luminous green eyes. When she walks, a shimmering gale wraps around her, flecked with upset motes of blood that start red then slowly crystallize to green in midair, never touching the floor, and every step rings with the hum of the storm she keeps caged inside her ribs. The lash of that captive wind leaves hairline cuts across her arms and shoulders—she is always bleeding as the wind around her cuts her, though the droplets spiral in place instead of falling, transforming from red to green crystals as they hang suspended. Despite the chaos, she guards her allies with razor focus—layering wind wards, calming Lady Lightning's tempests, and whispering flight equations to anyone brave enough to listen."""
    char_type: str = "B"
    gacha_rarity: int = 5
    damage_type: str = "Wind"
    passives: list = field(default_factory=lambda: ["lady_wind_tempest_guard"])
    special_abilities: list = field(default_factory=lambda: [])
    ui: dict = field(default_factory=lambda: {"portrait": "/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/Experimentation/Python-idle-game/idle_game/assets/characters/lady_wind"})
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
