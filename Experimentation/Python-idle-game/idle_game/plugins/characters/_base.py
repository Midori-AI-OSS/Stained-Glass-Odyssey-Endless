"""Base character class for idle game plugins."""
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class IdleCharacter:
    """Base class for idle game character plugins."""
    
    plugin_type = "character"
    
    # Required attributes
    id: str = ""
    name: str = ""
    
    # Lore and description
    short_lore: str = ""
    full_lore: str = ""
    
    # Character type and rarity
    char_type: str = "C"
    gacha_rarity: int = 0
    
    # Combat attributes
    damage_type: str = "Physical"
    passives: List[str] = field(default_factory=list)
    special_abilities: List[str] = field(default_factory=list)
    
    # UI attributes
    ui: Dict[str, Any] = field(default_factory=dict)
    
    # Base stats
    base_stats: Dict[str, Any] = field(
        default_factory=lambda: {
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
        }
    )
    
    # Growth and metadata
    growth: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert character to dictionary format used by game state."""
        return {
            "id": self.id,
            "name": self.name,
            "short_lore": self.short_lore,
            "full_lore": self.full_lore,
            "char_type": self.char_type,
            "gacha_rarity": self.gacha_rarity,
            "damage_type": self.damage_type,
            "passives": self.passives[:],  # Copy lists
            "special_abilities": self.special_abilities[:],
            "ui": self.ui.copy(),
            "base_stats": self.base_stats.copy(),
            "growth": self.growth.copy(),
            "metadata": self.metadata.copy(),
        }
