"""
Unified summons system for the Midori AI AutoFighter game.

Provides a consistent framework for creating and managing summons across
characters, passives, cards, and relics.
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
import random
from typing import TYPE_CHECKING
from typing import Optional

from autofighter.stats import Stats
from plugins.damage_types import get_damage_type
from plugins.damage_types import random_damage_type
from plugins.damage_types._base import DamageTypeBase

if TYPE_CHECKING:
    from autofighter.effects import HealingOverTime
    from autofighter.effects import StatModifier
    from autofighter.stat_effect import StatEffect

log = logging.getLogger(__name__)


@dataclass
class Summon(Stats):
    """Represents a summoned entity with proper stat inheritance."""

    # Summon-specific properties
    instance_id: str = ""
    summoner_id: str = ""
    summon_type: str = "generic"
    summon_source: str = "unknown"  # card/passive/relic that created this
    is_temporary: bool = True
    turns_remaining: int = -1  # -1 for permanent, >0 for temporary

    def __post_init__(self):
        """Initialize summon with proper inheritance from summoner."""
        super().__post_init__()
        # Mark this as a summon for identification
        if not hasattr(self, 'id') or not self.id:
            self.id = f"{self.summoner_id}_{self.summon_type}_summon"
        if not getattr(self, "instance_id", None):
            self.instance_id = ""

    @classmethod
    async def create_from_summoner(
        cls,
        summoner: Stats,
        summon_type: str = "generic",
        source: str = "unknown",
        stat_multiplier: float = 0.5,
        turns_remaining: int = -1,
        override_damage_type: Optional[DamageTypeBase] = None,
    ) -> "Summon":
        """Create a summon based on a summoner's stats.

        Args:
            summoner: The entity summoning this
            summon_type: Type identifier for the summon
            source: Source that created this summon (card/passive/relic name)
            stat_multiplier: Multiplier for inherited stats (default 0.5 = 50%)
            turns_remaining: How many turns this summon lasts (-1 = permanent)
            override_damage_type: Specific damage type, or None for random
        """
        # Calculate base stats at specified multiplier
        base_hp = int(summoner.max_hp * stat_multiplier)
        base_atk = int(summoner.atk * stat_multiplier)
        base_def = int(summoner._base_defense * stat_multiplier)

        # Determine damage type - high chance to match summoner, otherwise random
        if override_damage_type:
            damage_type = override_damage_type
        else:
            # 70% chance to match summoner's element, 30% chance for random
            if random.random() < 0.7 and hasattr(summoner, 'damage_type'):
                try:
                    # Try to get the same damage type as summoner
                    summoner_element = getattr(summoner.damage_type, 'id', 'Generic')
                    damage_type = get_damage_type(summoner_element)
                except Exception:
                    # Fallback to random if summoner's type is problematic
                    damage_type = random_damage_type()
            else:
                damage_type = random_damage_type()

        # Create the summon instance
        summon = cls(
            hp=base_hp,
            # Inherit damage type
            damage_type=damage_type,
            # Summon-specific properties
            summoner_id=getattr(summoner, 'id', str(id(summoner))),
            summon_type=summon_type,
            summon_source=source,
            turns_remaining=turns_remaining,
        )

        # Set base stats after creation (since they're init=False)
        summon._base_max_hp = base_hp
        summon._base_atk = base_atk
        summon._base_defense = base_def
        summon.hp = summon.max_hp
        # Inherit other relevant stats at same multiplier
        summon._base_crit_rate = summoner.crit_rate * stat_multiplier
        summon._base_crit_damage = summoner.crit_damage * stat_multiplier
        summon._base_effect_hit_rate = summoner.effect_hit_rate * stat_multiplier
        summon._base_effect_resistance = summoner.effect_resistance * stat_multiplier
        summon._base_mitigation = summoner._base_mitigation * stat_multiplier
        summon._base_vitality = summoner._base_vitality * stat_multiplier

        # Copy summoner's passives at reduced effectiveness if applicable
        if hasattr(summoner, 'passives') and summoner.passives:
            # Only copy certain "safe" passives that make sense for summons
            safe_passives = ['critical_boost', 'elemental_affinity']  # Add more as needed
            summon.passives = [p for p in summoner.passives if any(sp in p for sp in safe_passives)]

        # Share beneficial effects (buffs and HOTs) from summoner but not debuffs or DOTs
        await cls._share_beneficial_effects(summoner, summon, stat_multiplier)

        log.debug(f"Created {summon_type} summon for {summoner.id} with {stat_multiplier*100}% stats")

        return summon

    @classmethod
    async def _share_beneficial_effects(
        cls,
        summoner: Stats,
        summon: "Summon",
        stat_multiplier: float
    ) -> None:
        """Share beneficial effects (buffs and HOTs) from summoner to summon.

        Args:
            summoner: The entity creating the summon
            summon: The newly created summon
            stat_multiplier: Multiplier to apply to effect strength
        """
        # Copy beneficial StatEffects from summoner's active effects
        if hasattr(summoner, '_active_effects') and summoner._active_effects:
            for effect in summoner._active_effects:
                if cls._is_beneficial_stat_effect(effect):
                    # Create a scaled copy of the effect for the summon
                    scaled_effect = cls._scale_stat_effect(effect, stat_multiplier)
                    summon.add_effect(scaled_effect)
                    log.debug(f"Shared beneficial StatEffect '{effect.name}' to summon {summon.id}")

        # Copy HOTs and beneficial StatModifiers from effect manager if available
        if hasattr(summoner, 'effect_manager') and summoner.effect_manager:
            effect_mgr = summoner.effect_manager

            # Ensure summon has an effect manager
            if not hasattr(summon, 'effect_manager') or not summon.effect_manager:
                from autofighter.effects import EffectManager
                summon.effect_manager = EffectManager(summon)

            # Copy all HOTs (healing over time effects are inherently beneficial)
            for hot in effect_mgr.hots:
                scaled_hot = cls._scale_hot_effect(hot, stat_multiplier)
                await summon.effect_manager.add_hot(scaled_hot)
                log.debug(f"Shared HOT '{hot.name}' to summon {summon.id}")

            # Copy beneficial StatModifiers (buffs)
            for mod in effect_mgr.mods:
                if cls._is_beneficial_stat_modifier(mod):
                    scaled_mod = cls._scale_stat_modifier(mod, summon, stat_multiplier)
                    scaled_mod.apply()  # Apply the modifier to ensure it affects the summon's stats
                    await summon.effect_manager.add_modifier(scaled_mod)
                    log.debug(f"Shared beneficial StatModifier '{mod.name}' to summon {summon.id}")

    @classmethod
    def _is_beneficial_stat_effect(cls, effect: "StatEffect") -> bool:
        """Check if a StatEffect is beneficial (positive modifiers)."""
        if not effect.stat_modifiers:
            return False

        # Consider an effect beneficial if most of its modifiers are positive
        # Some stats like "damage_taken" would be beneficial if negative, but those are rare
        positive_count = 0
        total_count = 0

        for stat_name, value in effect.stat_modifiers.items():
            total_count += 1
            # Most stats are beneficial when positive
            if value > 0:
                positive_count += 1
            # Special case: damage_taken is beneficial when negative
            elif stat_name in ['damage_taken'] and value < 0:
                positive_count += 1

        return positive_count > total_count / 2

    @classmethod
    def _is_beneficial_stat_modifier(cls, modifier: "StatModifier") -> bool:
        """Check if a StatModifier is beneficial."""
        beneficial = False

        # Check deltas (additive modifiers)
        if modifier.deltas:
            for stat_name, value in modifier.deltas.items():
                if value > 0:
                    beneficial = True
                elif stat_name in ['damage_taken'] and value < 0:
                    beneficial = True

        # Check multipliers (multiplicative modifiers > 1.0 are beneficial)
        if modifier.multipliers:
            for stat_name, value in modifier.multipliers.items():
                if value > 1.0:
                    beneficial = True
                elif stat_name in ['damage_taken'] and value < 1.0:
                    beneficial = True

        return beneficial

    @classmethod
    def _scale_stat_effect(cls, effect: "StatEffect", multiplier: float) -> "StatEffect":
        """Create a scaled copy of a StatEffect."""
        from autofighter.stat_effect import StatEffect

        scaled_modifiers = {}
        for stat_name, value in effect.stat_modifiers.items():
            scaled_modifiers[stat_name] = value * multiplier

        return StatEffect(
            name=f"summon_{effect.name}",
            stat_modifiers=scaled_modifiers,
            duration=effect.duration,
            source=f"inherited_from_{effect.source}"
        )

    @classmethod
    def _scale_hot_effect(cls, hot: "HealingOverTime", multiplier: float) -> "HealingOverTime":
        """Create a scaled copy of a HealingOverTime effect."""
        from autofighter.effects import HealingOverTime

        return HealingOverTime(
            name=f"summon_{hot.name}",
            healing=int(hot.healing * multiplier),
            turns=hot.turns,
            id=f"summon_{hot.id}",
            source=hot.source
        )

    @classmethod
    def _scale_stat_modifier(cls, modifier: "StatModifier", summon: "Summon", multiplier: float) -> "StatModifier":
        """Create a scaled copy of a StatModifier for the summon."""
        from autofighter.effects import StatModifier

        scaled_deltas = None
        scaled_multipliers = None

        if modifier.deltas:
            scaled_deltas = {k: v * multiplier for k, v in modifier.deltas.items()}

        if modifier.multipliers:
            # For multipliers, scale the "bonus" part: if mult=1.5, bonus=0.5, scaled_bonus=0.5*mult, new_mult=1+scaled_bonus
            scaled_multipliers = {}
            for k, v in modifier.multipliers.items():
                bonus = v - 1.0
                scaled_bonus = bonus * multiplier
                scaled_multipliers[k] = 1.0 + scaled_bonus

        scaled_mod = StatModifier(
            stats=summon,  # Use the summon as the stats object
            name=f"summon_{modifier.name}",
            turns=modifier.turns,
            id=f"summon_{modifier.id}",
            deltas=scaled_deltas,
            multipliers=scaled_multipliers,
            bypass_diminishing=modifier.bypass_diminishing
        )

        return scaled_mod

    def tick_turn(self) -> bool:
        """Process a turn for this summon. Returns False if summon should be removed."""
        if self.turns_remaining > 0:
            self.turns_remaining -= 1
            if self.turns_remaining <= 0:
                log.debug(f"Summon {self.id} expired")
                return False
        return True

    def is_expired(self) -> bool:
        """Check if this summon has expired."""
        return self.turns_remaining == 0


