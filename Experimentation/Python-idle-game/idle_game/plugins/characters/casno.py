"""Character plugin: Casno."""
from dataclasses import dataclass, field
from plugins.characters._base import IdleCharacter


@dataclass
class Casno(IdleCharacter):
    """Character: Casno."""
    
    id: str = "casno"
    name: str = "Casno"
    short_lore: str = """A stoic veteran pyrokinetic who weaponizes recovery, taking tactical breaths to heal and strengthen before erupting back into combat."""
    full_lore: str = """A stoic veteran pyrokinetic who has learned to weaponize recovery. Casno tallies Relaxed stacks with every five attacks; once the gauge overflows, he skips his next strike to breathe, cashing in five stacks for a self-heal and 15% base-stat boons per stack before erupting back into combat."""
    char_type: str = "A"
    gacha_rarity: int = 5
    damage_type: str = "load_damage_type"
    passives: list = field(default_factory=lambda: ["casno_phoenix_respite"])
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
