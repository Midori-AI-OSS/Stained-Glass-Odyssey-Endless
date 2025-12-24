"""Core stats system for characters and entities.

This module provides the Stats class which handles all stat calculations,
damage/healing, effects, and combat mechanics. Ported from backend with
adaptations for Qt-based tick system (no async/await).
"""

from dataclasses import dataclass
from dataclasses import field
import enum
import math
import random
import sys
from typing import Any
from typing import Dict
from typing import Optional
from typing import Union

from .stat_effect import StatEffect

# Global enrage percentage applied during battles
_ENRAGE_PERCENT: float = 0.0

# Starting value for action gauges
GAUGE_START: int = 10_000


class CharacterType(enum.Enum):
    """Character type classification."""
    A = "A"
    B = "B"
    C = "C"


def set_enrage_percent(value: float) -> None:
    """Set global enrage percent (e.g., 0.15 for +15% damage taken, -15% healing)."""
    global _ENRAGE_PERCENT
    try:
        _ENRAGE_PERCENT = max(float(value), 0.0)
    except Exception:
        _ENRAGE_PERCENT = 0.0


def get_enrage_percent() -> float:
    """Get current global enrage percentage."""
    return _ENRAGE_PERCENT


@dataclass
class Stats:
    """Core stats container with damage/healing calculations.

    This class manages all character stats including base values, modifiers
    from effects, damage calculation, healing, gauges, and combat state.
    Designed for tick-based gameplay (10 ticks/second).
    """

    # Core progression stats
    hp: int = 1000
    exp: int = 0
    level: int = 1
    exp_multiplier: float = 1.0

    # Base stats (use properties for runtime access with effects)
    _base_max_hp: int = field(default=1000, init=False)
    _base_atk: int = field(default=200, init=False)
    _base_defense: int = field(default=200, init=False)
    _base_crit_rate: float = field(default=0.05, init=False)
    _base_crit_damage: float = field(default=2.0, init=False)
    _base_mitigation: float = field(default=1.0, init=False)
    _base_regain: int = field(default=100, init=False)
    _base_dodge_odds: float = field(default=0.05, init=False)
    _base_vitality: float = field(default=1.0, init=False)
    _base_spd: int = field(default=10, init=False)

    # Combat tracking
    damage_taken_total: int = 0
    damage_dealt_total: int = 0
    last_damage_taken: int = 0
    last_shield_absorbed: int = 0

    # Aggro system
    base_aggro: float = 0.1
    aggro_modifier: float = 0.0

    # Action queue
    action_gauge: int = GAUGE_START

    # Overheal/shields system
    overheal_enabled: bool = field(default=False, init=False)
    shields: int = field(default=0, init=False)

    # Effects system
    _active_effects: list[StatEffect] = field(default_factory=list, init=False)

    # Damage type (stored as string for now, plugin system comes later)
    damage_type: str = "Generic"

    def __post_init__(self):
        """Initialize derived values and ensure consistency."""
        # Only set HP to max_hp if it wasn't explicitly set
        if not hasattr(self, '_hp_initialized'):
            # Check if hp was passed as a parameter (not default 1000)
            # by seeing if it differs from the property access
            pass  # HP is already set from dataclass init

    # === PROPERTY ACCESSORS (Base + Effects) ===

    @property
    def max_hp(self) -> int:
        """Calculate runtime max HP (base + effects)."""
        return int(self._base_max_hp + self._calculate_stat_modifier('max_hp'))

    @max_hp.setter
    def max_hp(self, value: int) -> None:
        self._base_max_hp = int(value)
        if self.hp > value:
            self.hp = value

    @property
    def atk(self) -> int:
        """Calculate runtime attack (base + effects)."""
        return int(self._base_atk + self._calculate_stat_modifier('atk'))

    @atk.setter
    def atk(self, value: int) -> None:
        self._base_atk = int(value)

    @property
    def defense(self) -> int:
        """Calculate runtime defense (base + effects)."""
        return int(self._base_defense + self._calculate_stat_modifier('defense'))

    @defense.setter
    def defense(self, value: int) -> None:
        self._base_defense = int(value)

    @property
    def crit_rate(self) -> float:
        """Calculate runtime crit rate (base + effects), clamped to [0, 1]."""
        return max(0.0, min(1.0, self._base_crit_rate +
                           self._calculate_stat_modifier('crit_rate')))

    @crit_rate.setter
    def crit_rate(self, value: float) -> None:
        self._base_crit_rate = float(value)

    @property
    def crit_damage(self) -> float:
        """Calculate runtime crit damage multiplier (base + effects)."""
        return max(1.0, self._base_crit_damage +
                  self._calculate_stat_modifier('crit_damage'))

    @crit_damage.setter
    def crit_damage(self, value: float) -> None:
        self._base_crit_damage = float(value)

    @property
    def mitigation(self) -> float:
        """Calculate runtime mitigation (base + effects)."""
        return max(0.1, self._base_mitigation +
                  self._calculate_stat_modifier('mitigation'))

    @mitigation.setter
    def mitigation(self, value: float) -> None:
        self._base_mitigation = float(value)

    @property
    def regain(self) -> int:
        """Calculate runtime regain (HP regen per tick, base + effects)."""
        return int(max(0, self._base_regain +
                      self._calculate_stat_modifier('regain')))

    @regain.setter
    def regain(self, value: int) -> None:
        self._base_regain = int(value)

    @property
    def dodge_odds(self) -> float:
        """Calculate runtime dodge odds (base + effects), clamped to [0, 1]."""
        return max(0.0, min(1.0, self._base_dodge_odds +
                           self._calculate_stat_modifier('dodge_odds')))

    @dodge_odds.setter
    def dodge_odds(self, value: float) -> None:
        self._base_dodge_odds = float(value)

    @property
    def vitality(self) -> float:
        """Calculate runtime vitality (base + effects)."""
        return max(0.01, self._base_vitality +
                  self._calculate_stat_modifier('vitality'))

    @vitality.setter
    def vitality(self, value: float) -> None:
        self._base_vitality = float(value)

    @property
    def spd(self) -> int:
        """Calculate runtime speed (base + effects)."""
        return int(max(1, self._base_spd + self._calculate_stat_modifier('spd')))

    @spd.setter
    def spd(self, value: int) -> None:
        self._base_spd = int(value)

    @property
    def aggro(self) -> float:
        """Calculate current aggro score."""
        try:
            defense_term = (self.defense - self._base_defense) / self._base_defense
        except ZeroDivisionError:
            defense_term = 0.0
        modifier = self.aggro_modifier + self._calculate_stat_modifier("aggro_modifier")
        return self.base_aggro * (1 + modifier + defense_term)

    @property
    def effective_hp(self) -> int:
        """Get total effective HP (actual HP + shields)."""
        return self.hp + self.shields

    def _calculate_stat_modifier(self, stat_name: str) -> Union[int, float]:
        """Calculate total modifier for a stat from all active effects."""
        total: float = 0.0
        for effect in self._active_effects:
            if stat_name in effect.stat_modifiers:
                total += effect.stat_modifiers[stat_name]
        return total

    # === EFFECT MANAGEMENT ===

    def add_effect(self, effect: StatEffect) -> None:
        """Add a stat effect. Replaces any existing effect with same name."""
        self.remove_effect_by_name(effect.name)
        self._active_effects.append(effect)

    def remove_effect_by_name(self, effect_name: str) -> bool:
        """Remove effect by name. Returns True if removed."""
        initial_count = len(self._active_effects)
        self._active_effects = [e for e in self._active_effects
                               if e.name != effect_name]
        return len(self._active_effects) < initial_count

    def remove_effect_by_source(self, source: str) -> int:
        """Remove all effects from a source. Returns count removed."""
        initial_count = len(self._active_effects)
        self._active_effects = [e for e in self._active_effects
                               if e.source != source]
        return initial_count - len(self._active_effects)

    def tick_effects(self) -> None:
        """Update temporary effects, removing expired ones."""
        for effect in self._active_effects:
            effect.tick()
        self._active_effects = [e for e in self._active_effects
                               if not e.is_expired()]

    def get_active_effects(self) -> list[StatEffect]:
        """Get copy of all active effects."""
        return self._active_effects.copy()

    def clear_all_effects(self) -> None:
        """Remove all active effects."""
        self._active_effects.clear()

    # === DAMAGE SYSTEM ===

    def take_damage(self, amount: float, attacker: Optional["Stats"] = None) -> int:
        """Apply damage with full mitigation, crit, dodge, and shield logic.

        Returns actual HP damage dealt (after shields).
        """
        if self.hp <= 0:
            return 0

        # Check dodge
        if attacker is not None and random.random() < self.dodge_odds:
            self.last_damage_taken = 0
            self.last_shield_absorbed = 0
            return 0

        # Check crit from attacker
        if attacker is not None and random.random() < attacker.crit_rate:
            amount *= attacker.crit_damage

        # Apply mitigation formula (preserved from backend)
        src_vitality = attacker.vitality if attacker else 1.0
        defense_term = max(self.defense ** 3, 1)

        # Avoid division by zero
        vit = max(self.vitality, 1e-6)
        mit = max(self.mitigation, 1e-6)

        denom = defense_term * vit * mit
        growth_term = src_vitality / denom

        # Apply mitigation with safe capping
        safe_cap = math.sqrt(sys.float_info.max / growth_term) if growth_term > 0 else amount
        mitigated_amount = min(amount, safe_cap)
        mitigated_amount = ((mitigated_amount ** 2) * src_vitality) / denom

        # Apply enrage (increases damage taken)
        enr = get_enrage_percent()
        if enr > 0:
            mitigated_amount *= (1.0 + enr)

        # Final damage before shields (minimum 1 if any damage was attempted)
        total_damage = max(int(mitigated_amount), 1)

        # Apply to shields first, then HP
        shield_absorbed = 0
        hp_damage = 0

        if self.shields > 0:
            shield_absorbed = min(total_damage, self.shields)
            self.shields -= shield_absorbed
            total_damage -= shield_absorbed

        if total_damage > 0:
            hp_damage = min(total_damage, self.hp)
            self.hp = max(self.hp - hp_damage, 0)

        # Track damage
        self.last_damage_taken = hp_damage
        self.last_shield_absorbed = shield_absorbed
        self.damage_taken_total += hp_damage

        if attacker:
            attacker.damage_dealt_total += hp_damage

        return hp_damage

    def heal(self, amount: int, healer: Optional["Stats"] = None) -> int:
        """Apply healing with vitality scaling and overheal support.

        Returns actual healing applied.
        """
        # Apply vitality scaling
        src_vitality = healer.vitality if healer else 1.0
        scaled_amount = amount * src_vitality * self.vitality

        # Apply enrage (reduces healing)
        enr = get_enrage_percent()
        if enr > 0:
            scaled_amount *= max(1.0 - enr, 0.0)

        final_amount = max(1, int(scaled_amount))

        # Apply healing with overheal support
        if self.overheal_enabled:
            if self.hp < self.max_hp:
                # Heal normal HP first
                normal_heal = min(final_amount, self.max_hp - self.hp)
                self.hp += normal_heal
                final_amount -= normal_heal

            # Remaining becomes shields (with diminishing returns if already overhealed)
            if final_amount > 0:
                if self.shields > 0:
                    # Diminishing returns: 20% effectiveness when overhealed
                    final_amount = int(final_amount * 0.2)
                self.shields += final_amount
        else:
            # Standard healing - cap at max HP
            old_hp = self.hp
            self.hp = min(self.hp + final_amount, self.max_hp)
            final_amount = self.hp - old_hp

        return final_amount

    # === GAUGE SYSTEM ===

    def advance_gauge(self, amount: int) -> None:
        """Advance action gauge by amount (based on speed)."""
        self.action_gauge += amount

    def reset_gauge(self) -> None:
        """Reset gauge to starting value."""
        self.action_gauge = GAUGE_START

    # === CHARACTER DICT INTEGRATION ===

    @classmethod
    def from_character_dict(cls, char_data: Dict[str, Any]) -> "Stats":
        """Create Stats instance from prototype character dictionary.

        Args:
            char_data: Character dict with 'base_stats' and 'runtime' keys

        Returns:
            Stats instance populated from character data
        """
        base_stats = char_data.get("base_stats", {})
        runtime = char_data.get("runtime", {})

        stats = cls(
            exp=runtime.get("exp", 0),
            level=runtime.get("level", 1),
            exp_multiplier=runtime.get("exp_multiplier", 1.0),
            damage_type=char_data.get("damage_type", "Generic"),
        )

        # Set base stats from base_stats
        stats._base_max_hp = base_stats.get("max_hp", 1000)
        stats._base_atk = base_stats.get("atk", 200)
        stats._base_defense = base_stats.get("defense", 200)
        stats._base_crit_rate = base_stats.get("crit_rate", 0.05)
        stats._base_crit_damage = base_stats.get("crit_damage", 2.0)
        stats._base_mitigation = base_stats.get("mitigation", 1.0)
        stats._base_regain = base_stats.get("regain", 100)
        stats._base_dodge_odds = base_stats.get("dodge_odds", 0.05)
        stats._base_vitality = base_stats.get("vitality", 1.0)
        stats._base_spd = base_stats.get("spd", 10)

        # Set HP from runtime (after base stats are set so max_hp is correct)
        stats.hp = runtime.get("hp", stats.max_hp)

        return stats

    def to_character_dict_update(self) -> Dict[str, Any]:
        """Generate updates to apply back to character dictionary.

        Returns:
            Dictionary with runtime updates to merge into character data
        """
        return {
            "runtime": {
                "hp": self.hp,
                "exp": self.exp,
                "level": self.level,
                "exp_multiplier": self.exp_multiplier,
                "max_hp": self.max_hp,
            }
        }

    # === UTILITY METHODS ===

    def enable_overheal(self) -> None:
        """Enable overheal/shields (typically from relic/card effects)."""
        self.overheal_enabled = True

    def disable_overheal(self) -> None:
        """Disable overheal/shields and remove existing shields."""
        self.overheal_enabled = False
        self.shields = 0

    def calculate_crit(self) -> tuple[bool, float]:
        """Check if attack crits and return multiplier.

        Returns:
            (is_crit, damage_multiplier)
        """
        if random.random() < self.crit_rate:
            return (True, self.crit_damage)
        return (False, 1.0)
