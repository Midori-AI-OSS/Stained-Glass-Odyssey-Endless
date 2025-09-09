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
from typing import ClassVar
from typing import Dict
from typing import List
from typing import Optional

from autofighter.stats import BUS
from autofighter.stats import Stats
from plugins.damage_types import get_damage_type
from plugins.damage_types import random_damage_type
from plugins.damage_types._base import DamageTypeBase

if TYPE_CHECKING:
    from autofighter.effects import HealingOverTime
    from autofighter.effects import StatModifier
    from autofighter.party import Party
    from autofighter.stats import StatEffect

log = logging.getLogger(__name__)


@dataclass
class Summon(Stats):
    """Represents a summoned entity with proper stat inheritance."""

    # Summon-specific properties
    summoner_id: str = ""
    summon_type: str = "generic"
    summon_source: str = "unknown"  # card/passive/relic that created this
    is_temporary: bool = True
    turns_remaining: int = -1  # -1 for permanent, >0 for temporary

    def __post_init__(self):
        """Initialize summon with proper inheritance from summoner."""
        super().__post_init__()
        # Mark this as a summon for identification
        if not hasattr(self, "id") or not self.id:
            self.id = f"{self.summoner_id}_{self.summon_type}_summon"

    @classmethod
    def create_from_summoner(
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
            if random.random() < 0.7 and hasattr(summoner, "damage_type"):
                try:
                    # Try to get the same damage type as summoner
                    summoner_element = getattr(summoner.damage_type, "id", "Generic")
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
            summoner_id=getattr(summoner, "id", str(id(summoner))),
            summon_type=summon_type,
            summon_source=source,
            turns_remaining=turns_remaining,
        )

        # Set base stats after creation (since they're init=False)
        summon._base_max_hp = base_hp
        summon._base_atk = base_atk
        summon._base_defense = base_def
        # Inherit other relevant stats at same multiplier
        summon._base_crit_rate = summoner.crit_rate * stat_multiplier
        summon._base_crit_damage = summoner.crit_damage * stat_multiplier
        summon._base_effect_hit_rate = summoner.effect_hit_rate * stat_multiplier
        summon._base_effect_resistance = summoner.effect_resistance * stat_multiplier
        summon._base_mitigation = summoner._base_mitigation * stat_multiplier
        summon._base_vitality = summoner._base_vitality * stat_multiplier

        # Copy summoner's passives at reduced effectiveness if applicable
        if hasattr(summoner, "passives") and summoner.passives:
            # Only copy certain "safe" passives that make sense for summons
            safe_passives = [
                "critical_boost",
                "elemental_affinity",
            ]  # Add more as needed
            summon.passives = [
                p for p in summoner.passives if any(sp in p for sp in safe_passives)
            ]

        # Share beneficial effects (buffs and HOTs) from summoner but not debuffs or DOTs
        cls._share_beneficial_effects(summoner, summon, stat_multiplier)

        log.debug(
            f"Created {summon_type} summon for {summoner.id} with {stat_multiplier*100}% stats"
        )

        return summon

    @classmethod
    def _share_beneficial_effects(
        cls, summoner: Stats, summon: "Summon", stat_multiplier: float
    ) -> None:
        """Share beneficial effects (buffs and HOTs) from summoner to summon.

        Args:
            summoner: The entity creating the summon
            summon: The newly created summon
            stat_multiplier: Multiplier to apply to effect strength
        """
        # Copy beneficial StatEffects from summoner's active effects
        if hasattr(summoner, "_active_effects") and summoner._active_effects:
            for effect in summoner._active_effects:
                if cls._is_beneficial_stat_effect(effect):
                    # Create a scaled copy of the effect for the summon
                    scaled_effect = cls._scale_stat_effect(effect, stat_multiplier)
                    summon.add_effect(scaled_effect)
                    log.debug(
                        f"Shared beneficial StatEffect '{effect.name}' to summon {summon.id}"
                    )

        # Copy HOTs and beneficial StatModifiers from effect manager if available
        if hasattr(summoner, "effect_manager") and summoner.effect_manager:
            effect_mgr = summoner.effect_manager

            # Ensure summon has an effect manager
            if not hasattr(summon, "effect_manager") or not summon.effect_manager:
                from autofighter.effects import EffectManager

                summon.effect_manager = EffectManager(summon)

            # Copy all HOTs (healing over time effects are inherently beneficial)
            for hot in effect_mgr.hots:
                scaled_hot = cls._scale_hot_effect(hot, stat_multiplier)
                summon.effect_manager.add_hot(scaled_hot)
                log.debug(f"Shared HOT '{hot.name}' to summon {summon.id}")

            # Copy beneficial StatModifiers (buffs)
            for mod in effect_mgr.mods:
                if cls._is_beneficial_stat_modifier(mod):
                    scaled_mod = cls._scale_stat_modifier(mod, summon, stat_multiplier)
                    scaled_mod.apply()  # Apply the modifier to ensure it affects the summon's stats
                    summon.effect_manager.add_modifier(scaled_mod)
                    log.debug(
                        f"Shared beneficial StatModifier '{mod.name}' to summon {summon.id}"
                    )

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
            elif stat_name in ["damage_taken"] and value < 0:
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
                elif stat_name in ["damage_taken"] and value < 0:
                    beneficial = True

        # Check multipliers (multiplicative modifiers > 1.0 are beneficial)
        if modifier.multipliers:
            for stat_name, value in modifier.multipliers.items():
                if value > 1.0:
                    beneficial = True
                elif stat_name in ["damage_taken"] and value < 1.0:
                    beneficial = True

        return beneficial

    @classmethod
    def _scale_stat_effect(
        cls, effect: "StatEffect", multiplier: float
    ) -> "StatEffect":
        """Create a scaled copy of a StatEffect."""
        from autofighter.stats import StatEffect

        scaled_modifiers = {}
        for stat_name, value in effect.stat_modifiers.items():
            scaled_modifiers[stat_name] = value * multiplier

        return StatEffect(
            name=f"summon_{effect.name}",
            stat_modifiers=scaled_modifiers,
            duration=effect.duration,
            source=f"inherited_from_{effect.source}",
        )

    @classmethod
    def _scale_hot_effect(
        cls, hot: "HealingOverTime", multiplier: float
    ) -> "HealingOverTime":
        """Create a scaled copy of a HealingOverTime effect."""
        from autofighter.effects import HealingOverTime

        return HealingOverTime(
            name=f"summon_{hot.name}",
            healing=int(hot.healing * multiplier),
            turns=hot.turns,
            id=f"summon_{hot.id}",
            source=hot.source,
        )

    @classmethod
    def _scale_stat_modifier(
        cls, modifier: "StatModifier", summon: "Summon", multiplier: float
    ) -> "StatModifier":
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
            bypass_diminishing=modifier.bypass_diminishing,
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


class SummonManager:
    """Manages summons for the entire game."""

    # Class-level tracking of all active summons
    _active_summons: ClassVar[Dict[str, List[Summon]]] = {}
    _summon_limits: ClassVar[Dict[str, int]] = {}  # summoner_id -> max_summons
    _initialized: ClassVar[bool] = False

    @classmethod
    def initialize(cls):
        """Initialize the summon manager and event handlers."""
        if cls._initialized:
            return

        # Subscribe to battle events
        BUS.subscribe("battle_start", cls._on_battle_start)
        BUS.subscribe("battle_end", cls._on_battle_end)
        BUS.subscribe("turn_start", cls._on_turn_start)
        BUS.subscribe("turn_end", cls._on_turn_end)
        BUS.subscribe("entity_defeat", cls._on_entity_defeat)

        cls._initialized = True
        log.debug("SummonManager initialized")

    @classmethod
    def create_summon(
        cls,
        summoner: Stats,
        summon_type: str = "generic",
        source: str = "unknown",
        stat_multiplier: float = 0.5,
        turns_remaining: int = -1,
        override_damage_type: Optional[DamageTypeBase] = None,
        max_summons: int = 1,
        force_create: bool = False,
        min_health_threshold: float = 0.25,
    ) -> Optional[Summon]:
        """Create a new summon and add it to tracking.

        Args:
            summoner: The entity creating the summon
            summon_type: Type identifier for the summon
            source: Source creating this summon
            stat_multiplier: Stat inheritance multiplier
            turns_remaining: Duration (-1 = permanent)
            override_damage_type: Specific damage type
            max_summons: Maximum summons this summoner can have
            force_create: If True, bypass smart decision logic and create anyway
            min_health_threshold: Health threshold for existing summons to be considered viable

        Returns:
            The created summon, or None if limit exceeded or smart logic says not to create
        """
        cls.initialize()

        # SAFEGUARD: Prevent summons from creating more summons to avoid infinite chains
        if isinstance(summoner, Summon):
            log.warning(
                f"Summon {getattr(summoner, 'id', 'unknown')} attempted to create another summon - blocked for safety"
            )
            return None

        summoner_id = getattr(summoner, "id", str(id(summoner)))

        # Initialize tracking for this summoner if needed
        if summoner_id not in cls._active_summons:
            cls._active_summons[summoner_id] = []
            cls._summon_limits[summoner_id] = max_summons

        # Check summon limit
        if len(cls._active_summons[summoner_id]) >= max_summons:
            log.debug(f"Summon limit ({max_summons}) reached for {summoner_id}")

            # If we're at the limit and not forcing, check if we should replace existing summons
            if not force_create:
                decision = cls.should_resummon(summoner_id, min_health_threshold)
                if not decision["should_resummon"]:
                    log.info(
                        f"Skipping summon creation for {summoner_id}: {decision['reason']}"
                    )
                    return None
                else:
                    log.info(
                        f"Proceeding with summon replacement for {summoner_id}: {decision['reason']}"
                    )
                    # Remove the least viable existing summon to make room
                    existing_summons = cls.get_summons(summoner_id)
                    if existing_summons:
                        # Find the summon with lowest health percentage
                        worst_summon = min(
                            existing_summons,
                            key=lambda s: s.hp / s.max_hp if s.max_hp > 0 else 0,
                        )
                        cls.remove_summon(worst_summon, "replaced_by_healthier_summon")
            elif force_create:
                # Force creation by removing an existing summon
                existing_summons = cls._active_summons[summoner_id]
                if existing_summons:
                    old_summon = existing_summons[0]  # Remove first summon
                    cls.remove_summon(old_summon, "forced_replacement")
                else:
                    return None

        # Create the summon
        summon = Summon.create_from_summoner(
            summoner,
            summon_type,
            source,
            stat_multiplier,
            turns_remaining,
            override_damage_type,
        )

        # Add to tracking
        cls._active_summons[summoner_id].append(summon)

        # Emit creation event - batched for performance
        BUS.emit_batched("summon_created", summoner, summon, source)

        log.info(f"Created {summon_type} summon for {summoner_id} from {source}")
        return summon

    @classmethod
    def get_summons(cls, summoner_id: str) -> List[Summon]:
        """Get all active summons for a summoner."""
        return cls._active_summons.get(summoner_id, []).copy()

    @classmethod
    def evaluate_summon_viability(
        cls, summon: Summon, min_health_percent: float = 0.25
    ) -> dict:
        """Evaluate if a summon is still viable and worth keeping.

        Args:
            summon: The summon to evaluate
            min_health_percent: Minimum health percentage to consider viable (default 25%)

        Returns:
            Dict with viability assessment:
            {
                'viable': bool,  # Overall viability
                'health_good': bool,  # Health above threshold
                'time_remaining': int,  # Turns remaining (-1 for permanent)
                'expiring_soon': bool,  # Will expire in 1-2 turns
                'recommendation': str  # Human readable recommendation
            }
        """
        if not summon or summon.hp <= 0:
            return {
                "viable": False,
                "health_good": False,
                "time_remaining": 0,
                "expiring_soon": True,
                "recommendation": "Summon is dead or missing",
            }

        health_percent = summon.hp / summon.max_hp if summon.max_hp > 0 else 0
        health_good = health_percent >= min_health_percent

        time_remaining = summon.turns_remaining
        expiring_soon = time_remaining > 0 and time_remaining <= 2

        # Determine overall viability
        viable = health_good and not expiring_soon

        # Generate recommendation
        if not health_good:
            recommendation = f"Low health ({health_percent:.1%}), consider replacing"
        elif expiring_soon:
            recommendation = (
                f"Expiring in {time_remaining} turn(s), prepare replacement"
            )
        elif viable:
            recommendation = f"Healthy ({health_percent:.1%}), keep current summon"
        else:
            recommendation = "Unknown state"

        return {
            "viable": viable,
            "health_good": health_good,
            "time_remaining": time_remaining,
            "expiring_soon": expiring_soon,
            "recommendation": recommendation,
        }

    @classmethod
    def should_resummon(
        cls,
        summoner_id: str,
        min_health_threshold: float = 0.25,
        consider_expiration: bool = True,
    ) -> dict:
        """Determine if a summoner should create a new summon based on existing summon state.

        Args:
            summoner_id: ID of the summoner
            min_health_threshold: Minimum health percentage for summons to be considered viable
            consider_expiration: Whether to factor in summon expiration time

        Returns:
            Dict with recommendation:
            {
                'should_resummon': bool,  # Whether to create a new summon
                'reason': str,  # Reason for the recommendation
                'existing_summons': list,  # List of existing summon evaluations
                'viable_count': int  # Number of viable existing summons
            }
        """
        existing_summons = cls.get_summons(summoner_id)

        if not existing_summons:
            return {
                "should_resummon": True,
                "reason": "No existing summons",
                "existing_summons": [],
                "viable_count": 0,
            }

        # Evaluate each existing summon
        evaluations = []
        viable_count = 0

        for summon in existing_summons:
            eval_result = cls.evaluate_summon_viability(summon, min_health_threshold)
            evaluations.append(
                {
                    "summon_id": summon.id,
                    "summon_type": summon.summon_type,
                    "evaluation": eval_result,
                }
            )

            if eval_result["viable"]:
                viable_count += 1

        # Decision logic
        if viable_count > 0:
            reason = (
                f"Have {viable_count} viable summon(s), avoid unnecessary resummoning"
            )
            should_resummon = False
        else:
            # Check specific reasons why existing summons aren't viable
            low_health = any(not e["evaluation"]["health_good"] for e in evaluations)
            expiring = any(e["evaluation"]["expiring_soon"] for e in evaluations)

            if low_health and expiring:
                reason = "Existing summons are low health and expiring soon"
            elif low_health:
                reason = "Existing summons have low health"
            elif expiring:
                reason = "Existing summons are expiring soon"
            else:
                reason = "Existing summons are not viable"

            should_resummon = True

        return {
            "should_resummon": should_resummon,
            "reason": reason,
            "existing_summons": evaluations,
            "viable_count": viable_count,
        }

    @classmethod
    def remove_summon(cls, summon: Summon, reason: str = "unknown") -> bool:
        """Remove a summon from tracking."""
        summoner_id = summon.summoner_id
        if summoner_id in cls._active_summons:
            if summon in cls._active_summons[summoner_id]:
                cls._active_summons[summoner_id].remove(summon)
                BUS.emit_batched("summon_removed", summon, reason)
                log.debug(f"Removed summon {summon.id} due to {reason}")
                return True
        return False

    @classmethod
    def remove_all_summons(cls, summoner_id: str, reason: str = "cleanup") -> int:
        """Remove all summons for a summoner."""
        count = 0
        if summoner_id in cls._active_summons:
            summons = cls._active_summons[summoner_id].copy()
            for summon in summons:
                if cls.remove_summon(summon, reason):
                    count += 1
        return count

    @classmethod
    def get_all_summons(cls) -> List[Summon]:
        """Get all active summons across all summoners."""
        all_summons = []
        for summons in cls._active_summons.values():
            all_summons.extend(summons)
        return all_summons

    @classmethod
    def _on_battle_start(cls, *args, **kwargs):
        """Handle battle start - reset temporary tracking."""
        log.debug("Battle started - summon tracking active")

    @classmethod
    def _on_battle_end(cls, *args, **kwargs):
        """Handle battle end - clean up temporary summons."""
        total_removed = 0
        for summoner_id in list(cls._active_summons.keys()):
            summons = cls._active_summons[summoner_id].copy()
            for summon in summons:
                if summon.is_temporary:
                    cls.remove_summon(summon, "battle_end")
                    total_removed += 1

        # Clean up empty entries from dictionaries
        cls._cleanup_empty_entries()

        if total_removed > 0:
            log.debug(f"Cleaned up {total_removed} temporary summons at battle end")

    @classmethod
    def _on_turn_start(cls, entity, **kwargs):
        """Handle turn start - process summon turns."""
        entity_id = getattr(entity, "id", str(id(entity)))
        if entity_id in cls._active_summons:
            summons = cls._active_summons[entity_id].copy()
            for summon in summons:
                if not summon.tick_turn():
                    cls.remove_summon(summon, "expired")

    @classmethod
    def _on_turn_end(cls, entity, **kwargs):
        """Handle turn end for summons."""
        # Could add turn-end processing here if needed
        pass

    @classmethod
    def _on_entity_defeat(cls, entity, **kwargs):
        """Handle entity defeat - remove their summons."""
        entity_id = getattr(entity, "id", str(id(entity)))
        removed = cls.remove_all_summons(entity_id, "summoner_defeated")
        if removed > 0:
            log.debug(f"Removed {removed} summons due to summoner defeat")

    @classmethod
    def add_summons_to_party(cls, party: "Party") -> int:
        """Add all active summons to a party for battle. Returns number added."""
        added = 0
        all_summons = cls.get_all_summons()

        for summon in all_summons:
            # Check if summoner is in the party
            summoner_in_party = any(
                getattr(member, "id", str(id(member))) == summon.summoner_id
                for member in party.members
            )

            if summoner_in_party and summon not in party.members:
                party.members.append(summon)
                added += 1

        if added > 0:
            log.debug(f"Added {added} summons to party for battle")

        return added

    @classmethod
    def cleanup(cls):
        """Clean up all summons and reset manager."""
        cls._active_summons.clear()
        cls._summon_limits.clear()
        log.debug("SummonManager cleaned up")

    @classmethod
    def reset_all(cls):
        """Reset all summon tracking - clears both dictionaries."""
        cls._active_summons.clear()
        cls._summon_limits.clear()
        log.debug("SummonManager reset - all tracking cleared")

    @classmethod
    def _cleanup_empty_entries(cls):
        """Remove empty entries from tracking dictionaries."""
        # Remove summoners with no active summons
        empty_summoners = [
            summoner_id
            for summoner_id, summons in cls._active_summons.items()
            if not summons
        ]
        for summoner_id in empty_summoners:
            del cls._active_summons[summoner_id]
            # Also remove from limits if no summons remain
            cls._summon_limits.pop(summoner_id, None)

        if empty_summoners:
            log.debug(f"Cleaned up {len(empty_summoners)} empty summon entries")


# Initialize the manager when module is imported
SummonManager.initialize()
