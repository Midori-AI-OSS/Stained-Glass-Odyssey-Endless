"""Core effects system for temporary stat modifications and damage/healing over time.

This module provides the foundation for buffs, debuffs, and status effects.
Ported from backend with adaptations for tick-based Qt system (no async/await).
"""

from dataclasses import dataclass
from dataclasses import field
from typing import Dict
from typing import Optional
from typing import Union

from .stat_effect import StatEffect
from .stats import Stats

# Diminishing returns configuration for buff scaling
# Each stat has: (threshold, scaling_factor, base_offset)
DIMINISHING_RETURNS_CONFIG = {
    'max_hp': {'threshold': 500, 'scaling_factor': 1.05, 'base_offset': 50000},
    'hp': {'threshold': 500, 'scaling_factor': 1.05, 'base_offset': 50000},
    'atk': {'threshold': 100, 'scaling_factor': 2.0, 'base_offset': 1000},
    'spd': {'threshold': 100, 'scaling_factor': 2.0, 'base_offset': 1000},
    'defense': {'threshold': 100, 'scaling_factor': 2.0, 'base_offset': 1000},
    'mitigation': {'threshold': 0.01, 'scaling_factor': 100.0, 'base_offset': 2},
    'vitality': {'threshold': 0.01, 'scaling_factor': 100.0, 'base_offset': 2},
    'crit_rate': {'threshold': 0.01, 'scaling_factor': 2.0, 'base_offset': 5},
    'crit_damage': {'threshold': 5.0, 'scaling_factor': 1000.0, 'base_offset': 2.0},
}


def get_current_stat_value(stats: Stats, stat_name: str) -> Union[int, float]:
    """Get the current value of a stat from the Stats object."""
    stat_mapping = {
        'max_hp': lambda s: s.max_hp,
        'hp': lambda s: s.max_hp,
        'atk': lambda s: s.atk,
        'defense': lambda s: s.defense,
        'spd': lambda s: s.spd,
        'crit_rate': lambda s: s.crit_rate,
        'crit_damage': lambda s: s.crit_damage,
        'mitigation': lambda s: s.mitigation,
        'vitality': lambda s: s.vitality,
        'effect_hit_rate': lambda s: s.effect_hit_rate,
        'effect_resistance': lambda s: s.effect_resistance,
        'dodge_odds': lambda s: s.dodge_odds,
        'regain': lambda s: s.regain,
    }

    if stat_name in stat_mapping:
        return stat_mapping[stat_name](stats)

    return getattr(stats, stat_name, 0)


def calculate_diminishing_returns(stat_name: str, current_value: Union[int, float]) -> float:
    """Calculate diminishing returns scaling factor for buff effectiveness.

    Args:
        stat_name: Name of the stat being modified
        current_value: Current value of the stat

    Returns:
        Scaling factor between 0.000001 and 1.0 representing buff effectiveness
    """
    if stat_name not in DIMINISHING_RETURNS_CONFIG:
        return 1.0

    config = DIMINISHING_RETURNS_CONFIG[stat_name]
    threshold = config['threshold']
    scaling_factor = config['scaling_factor']
    base_offset = config['base_offset']

    effective_value = max(0, current_value - base_offset)
    epsilon = threshold * 1e-10
    steps = int((effective_value + epsilon) // threshold)

    if steps <= 0:
        return 1.0

    try:
        effectiveness = 1.0 / (scaling_factor ** steps)
        return max(1e-6, min(1.0, effectiveness))
    except (OverflowError, ZeroDivisionError):
        return 1e-6


@dataclass
class StatModifier:
    """Temporarily adjust stats via additive or multiplicative changes using StatEffect."""

    stats: Stats
    name: str
    turns: int
    id: str
    deltas: Optional[Dict[str, float]] = None
    multipliers: Optional[Dict[str, float]] = None
    bypass_diminishing: bool = False
    _effect_applied: bool = field(init=False, default=False)

    def apply(self) -> None:
        """Apply configured modifiers to the stats object using StatEffect with diminishing returns."""
        if self._effect_applied:
            return

        stat_modifiers = {}

        # Handle additive deltas with diminishing returns scaling
        for name, value in (self.deltas or {}).items():
            if self.bypass_diminishing:
                scaled_value = value
            else:
                current_value = get_current_stat_value(self.stats, name)
                scaling_factor = calculate_diminishing_returns(name, current_value)
                scaled_value = value * scaling_factor
            stat_modifiers[name] = stat_modifiers.get(name, 0) + scaled_value

        # Handle multiplicative changes by converting to additive
        for name, multiplier in (self.multipliers or {}).items():
            if hasattr(self.stats, name):
                if hasattr(self.stats, 'get_base_stat'):
                    base_value = self.stats.get_base_stat(name)
                else:
                    base_value = getattr(self.stats, name, 0)

                additive_change = base_value * (multiplier - 1.0)

                if self.bypass_diminishing:
                    scaled_change = additive_change
                else:
                    current_value = get_current_stat_value(self.stats, name)
                    scaling_factor = calculate_diminishing_returns(name, current_value)
                    scaled_change = additive_change * scaling_factor

                stat_modifiers[name] = stat_modifiers.get(name, 0) + scaled_change

        if stat_modifiers:
            effect = StatEffect(
                name=self.id,
                stat_modifiers=stat_modifiers,
                duration=self.turns if self.turns > 0 else -1,
                source=f"modifier_{self.name}"
            )

            self.stats.add_effect(effect)
            self._effect_applied = True

    def remove(self) -> None:
        """Remove the effect from stats if it was applied."""
        if self._effect_applied:
            self.stats.remove_effect_by_name(self.id)
            self._effect_applied = False

    def tick(self) -> bool:
        """Decrement remaining turns and remove when expired.

        Returns:
            True if effect is still active, False if expired
        """
        if self.turns <= 0:
            return True  # Permanent effect

        self.turns -= 1
        if self.turns <= 0:
            self.remove()
            return False
        return True


def create_stat_buff(
    stats: Stats,
    *,
    name: str = "buff",
    turns: int = 1,
    id: Optional[str] = None,
    bypass_diminishing: bool = False,
    **modifiers: float,
) -> StatModifier:
    """Create and apply a StatModifier to stats.

    Keyword arguments ending with _mult are treated as multipliers;
    others are additive deltas. The modifier is applied immediately.

    Args:
        stats: Target Stats object
        name: Display name for the buff
        turns: Duration in turns (0 = permanent)
        id: Unique identifier (defaults to name)
        bypass_diminishing: Skip diminishing returns calculation
        **modifiers: Stat modifications (atk=50, defense_mult=1.2, etc.)

    Returns:
        The created and applied StatModifier
    """
    deltas: Dict[str, float] = {}
    mults: Dict[str, float] = {}

    for key, value in modifiers.items():
        if key.endswith("_mult"):
            mults[key[:-5]] = float(value)
        else:
            deltas[key] = float(value)

    effect = StatModifier(
        stats=stats,
        name=name,
        turns=turns,
        id=id or name,
        deltas=deltas or None,
        multipliers=mults or None,
        bypass_diminishing=bypass_diminishing,
    )
    effect.apply()
    return effect


@dataclass
class DamageOverTime:
    """Base class for damage over time effects."""

    name: str
    damage: int
    turns: int
    id: str
    source: Optional[Stats] = None

    def tick(self, target: Stats) -> bool:
        """Apply damage for this turn.

        Args:
            target: Stats object to damage

        Returns:
            True if effect should continue, False if expired
        """
        if target.hp <= 0:
            self.turns = 0
            return False

        # Apply damage directly to HP (simplified, no damage type modifiers for now)
        dmg = max(1, int(self.damage))
        target.hp = max(0, target.hp - dmg)

        # Check if target died from the damage
        if target.hp <= 0:
            self.turns = 0
            return False

        self.turns -= 1
        return self.turns > 0


@dataclass
class HealingOverTime:
    """Base class for healing over time effects."""

    name: str
    healing: int
    turns: int
    id: str
    source: Optional[Stats] = None

    def tick(self, target: Stats) -> bool:
        """Apply healing for this turn.

        Args:
            target: Stats object to heal

        Returns:
            True if effect should continue, False if expired
        """
        if target.hp <= 0:
            self.turns = 0
            return False

        # Apply healing directly to HP (simplified)
        heal = max(1, int(self.healing))
        target.hp = min(target.max_hp, target.hp + heal)

        self.turns -= 1
        return self.turns > 0
