import asyncio
from dataclasses import dataclass
from dataclasses import field
import random
from typing import Callable
from typing import Optional
from typing import Union

from rich.console import Console

from autofighter.stat_effect import StatEffect
from autofighter.stats import Stats

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
    # Map common stat names to their property accessors
    stat_mapping = {
        'max_hp': lambda s: s.max_hp,
        'hp': lambda s: s.max_hp,  # Use max_hp for HP calculations
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

    # Fallback: try to get the attribute directly
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
        return 1.0  # No scaling for unconfigured stats

    config = DIMINISHING_RETURNS_CONFIG[stat_name]
    threshold = config['threshold']
    scaling_factor = config['scaling_factor']
    base_offset = config['base_offset']

    # Calculate how far above the base offset we are
    effective_value = max(0, current_value - base_offset)

    # Calculate number of complete threshold steps we've reached
    # Add small epsilon to handle floating point precision issues
    epsilon = threshold * 1e-10
    steps = int((effective_value + epsilon) // threshold)

    # TODO: Consider if these scaling factors are too aggressive for game balance
    # Currently: 4x for HP per 500, 100x for ATK/DEF per 100, etc.
    # Might need tuning based on gameplay feedback

    if steps <= 0:
        return 1.0  # Full effectiveness below first threshold

    # Calculate scaling: 1 / (scaling_factor ^ steps)
    try:
        effectiveness = 1.0 / (scaling_factor ** steps)
        # Clamp to prevent numerical issues
        return max(1e-6, min(1.0, effectiveness))
    except (OverflowError, ZeroDivisionError):
        # Fallback for extreme values
        return 1e-6


@dataclass
class StatModifier:
    """Temporarily adjust stats via additive or multiplicative changes using the new StatEffect system."""

    stats: Stats
    name: str
    turns: int
    id: str
    deltas: dict[str, float] | None = None
    multipliers: dict[str, float] | None = None
    _effect_applied: bool = field(init=False, default=False)
    bypass_diminishing: bool = False

    def apply(self) -> None:
        """Apply configured modifiers to the stats object using StatEffect with diminishing returns."""
        if self._effect_applied:
            return  # Already applied

        # Convert deltas and multipliers to a single stat_modifiers dict
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

        # Handle multiplicative changes by converting to additive with diminishing returns
        for name, multiplier in (self.multipliers or {}).items():
            if hasattr(self.stats, name):
                # Get base stat value for calculation
                if hasattr(self.stats, 'get_base_stat'):
                    base_value = self.stats.get_base_stat(name)
                else:
                    base_value = getattr(self.stats, name, 0)

                # Convert multiplier to additive value
                additive_change = base_value * (multiplier - 1.0)

                # Apply diminishing returns scaling to the additive change
                if self.bypass_diminishing:
                    scaled_change = additive_change
                else:
                    current_value = get_current_stat_value(self.stats, name)
                    scaling_factor = calculate_diminishing_returns(name, current_value)
                    scaled_change = additive_change * scaling_factor

                stat_modifiers[name] = stat_modifiers.get(name, 0) + scaled_change

        if stat_modifiers:
            # Create and apply StatEffect
            effect = StatEffect(
                name=self.id,
                stat_modifiers=stat_modifiers,
                duration=self.turns if self.turns > 0 else -1,  # -1 for permanent
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
        """Decrement remaining turns and remove when expired."""
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
    id: str | None = None,
    bypass_diminishing: bool = False,
    **modifiers: float,
) -> StatModifier:
    """Create and apply a :class:`StatModifier` to ``stats``.

    Keyword arguments ending with ``_mult`` are treated as multipliers for the
    corresponding stat; others are additive deltas. The new modifier is applied
    immediately and returned for tracking in an :class:`EffectManager`.
    """

    deltas: dict[str, float] = {}
    mults: dict[str, float] = {}
    for key, value in modifiers.items():
        if key.endswith("_mult"):
            mults[key[:-5]] = float(value)
        else:
            deltas[key] = float(value)
    # Pass through the bypass_diminishing parameter to StatModifier
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
    source: Stats | None = None

    async def tick(self, target: Stats, *_: object) -> bool:
        try:
            from autofighter.rooms.battle.pacing import YIELD_MULTIPLIER
            from autofighter.rooms.battle.pacing import pace_sleep
        except (ImportError, ModuleNotFoundError):
            YIELD_MULTIPLIER = 0.0

            async def pace_sleep(_multiplier: float = 1.0) -> None:
                await asyncio.sleep(0)

        from autofighter.stats import BUS  # Import here to avoid circular imports

        source_actor = self.source or target
        attacker_for_events = None
        if isinstance(self.source, Stats) and self.source is not target:
            attacker_for_events = self.source
        dtype = getattr(self, "damage_type", None)
        if dtype is None:
            dtype = getattr(source_actor, "damage_type", target.damage_type)
        dmg = dtype.on_dot_damage_taken(
            self.damage,
            source_actor,
            target,
        )
        dmg = dtype.on_party_dot_damage_taken(
            dmg,
            source_actor,
            target,
        )
        source_type = getattr(source_actor, "damage_type", None)
        if source_type is not dtype:
            dmg = source_type.on_party_dot_damage_taken(dmg, source_actor, target)

        dmg = max(1, int(dmg))

        # Emit DoT tick event before applying damage - async for better performance
        await BUS.emit_async("dot_tick", attacker_for_events, target, dmg, self.name, {
            "dot_id": self.id,
            "remaining_turns": self.turns - 1,
            "original_damage": self.damage
        })

        # Check if this DOT will kill the target
        target_hp_before = target.hp
        await target.apply_damage(
            dmg,
            attacker=attacker_for_events,
            trigger_on_hit=False,
        )

        # If target died from this DOT, emit a DOT kill event - async for better performance
        if target_hp_before > 0 and target.hp <= 0:
            await BUS.emit_async("dot_kill", attacker_for_events, target, dmg, self.name, {
                "dot_id": self.id,
                "dot_name": self.name,
                "final_damage": dmg
            })

        await pace_sleep(YIELD_MULTIPLIER)
        self.turns -= 1
        return self.turns > 0


@dataclass
class HealingOverTime:
    """Base class for healing over time effects."""

    name: str
    healing: int
    turns: int
    id: str
    source: Stats | None = None

    async def tick(self, target: Stats, *_: object) -> bool:
        try:
            from autofighter.rooms.battle.pacing import YIELD_MULTIPLIER
            from autofighter.rooms.battle.pacing import pace_sleep
        except (ImportError, ModuleNotFoundError):
            YIELD_MULTIPLIER = 0.0

            async def pace_sleep(_multiplier: float = 1.0) -> None:
                await asyncio.sleep(0)

        from autofighter.stats import BUS  # Import here to avoid circular imports

        if getattr(target, "hp", 0) <= 0:
            self.turns = 0
            return False

        healer = self.source or target
        dtype = getattr(self, "damage_type", None)
        if dtype is None:
            dtype = getattr(healer, "damage_type", target.damage_type)
        heal = dtype.on_hot_heal_received(self.healing, healer, target)
        heal = dtype.on_party_hot_heal_received(heal, healer, target)
        source_type = getattr(healer, "damage_type", None)
        if source_type is not dtype:
            heal = source_type.on_party_hot_heal_received(heal, healer, target)

        heal = max(1, int(heal))

        # Emit HoT tick event before applying healing - async for better performance
        await BUS.emit_async("hot_tick", healer, target, heal, self.name, {
            "hot_id": self.id,
            "remaining_turns": self.turns - 1,
            "original_healing": self.healing
        })

        await target.apply_healing(heal, healer=healer)
        await pace_sleep(YIELD_MULTIPLIER)
        self.turns -= 1
        return self.turns > 0


class EffectManager:
    """Manage DoT and HoT effects on a Stats object."""

    def __init__(self, stats: Stats, debug: bool = False) -> None:
        self.stats = stats
        self.dots: list[DamageOverTime] = []
        self.hots: list[HealingOverTime] = []
        self.mods: list[StatModifier] = []
        self._console = Console()
        self._debug = debug

    async def _log(self, message: str) -> None:
        """Write a log message without blocking the main loop."""
        await asyncio.to_thread(self._console.log, message)

    async def add_dot(self, effect: DamageOverTime, max_stacks: int | None = None) -> None:
        """Attach a DoT instance to the tracked stats.

        DoTs with the same ``id`` stack independently, allowing multiple
        copies to tick each turn.  When ``max_stacks`` is provided, extra
        applications beyond that limit are ignored rather than refreshed.
        """
        from autofighter.stats import BUS  # Import here to avoid circular imports

        # Don't add effects to dead characters
        if self.stats.hp <= 0:
            return

        if max_stacks is not None:
            current = len([d for d in self.dots if d.id == effect.id])
            if current >= max_stacks:
                return
        self.dots.append(effect)
        self.stats.dots.append(effect.id)

        # Emit effect applied event - batched for performance
        await BUS.emit_batched_async(
            "effect_applied",
            effect.name,
            self.stats,
            {
                "effect_type": "dot",
                "effect_id": effect.id,
                "damage": effect.damage,
                "turns": effect.turns,
                "current_stacks": len([d for d in self.dots if d.id == effect.id]),
            },
        )

    async def add_hot(self, effect: HealingOverTime) -> None:
        """Attach a HoT instance to the tracked stats.

        Healing effects simply accumulate; each copy heals separately every
        tick with no inherent stack cap.
        """
        from autofighter.stats import BUS  # Import here to avoid circular imports

        # Don't add effects to dead characters
        if self.stats.hp <= 0:
            return

        self.hots.append(effect)
        self.stats.hots.append(effect.id)

        # Emit effect applied event - batched for performance
        await BUS.emit_batched_async(
            "effect_applied",
            effect.name,
            self.stats,
            {
                "effect_type": "hot",
                "effect_id": effect.id,
                "healing": effect.healing,
                "turns": effect.turns,
                "current_stacks": len([h for h in self.hots if h.id == effect.id]),
            },
        )

    async def remove_hots(
        self,
        predicate: Callable[[HealingOverTime], bool],
    ) -> int:
        """Remove HoT instances matching ``predicate``.

        Returns the number of removed effects and emits ``effect_expired``
        events for each removal so UI hooks stay in sync.
        """
        from autofighter.stats import BUS  # Import here to avoid circular imports

        matching = [hot for hot in list(self.hots) if predicate(hot)]
        if not matching:
            return 0

        for hot in matching:
            if hot in self.hots:
                self.hots.remove(hot)

            if hasattr(self.stats, "hots"):
                while hot.id in self.stats.hots:
                    self.stats.hots.remove(hot.id)

        for hot in matching:
            await BUS.emit_async(
                "effect_expired",
                hot.name,
                self.stats,
                {
                    "effect_type": "hot",
                    "effect_id": hot.id,
                    "expired_naturally": False,
                },
            )

        return len(matching)

    async def add_modifier(self, effect: StatModifier) -> None:
        """Attach a stat modifier to the tracked stats."""
        from autofighter.stats import BUS  # Import here to avoid circular imports

        if any(existing is effect for existing in self.mods):
            self.mods[:] = [mod for mod in self.mods if mod is not effect]

        duplicates = [
            existing for existing in self.mods if existing.id == effect.id
        ]
        duplicates_removed = False
        for existing in duplicates:
            existing.remove()
            duplicates_removed = True

        if duplicates:
            self.mods[:] = [mod for mod in self.mods if mod not in duplicates]

        if duplicates_removed:
            effect._effect_applied = False

        if not effect._effect_applied:
            effect.apply()

        while effect.id in self.stats.mods:
            self.stats.mods.remove(effect.id)

        self.mods.append(effect)
        self.stats.mods.append(effect.id)

        # Emit effect applied event - batched for performance
        await BUS.emit_batched_async(
            "effect_applied",
            effect.name,
            self.stats,
            {
                "effect_type": "stat_modifier",
                "effect_id": effect.id,
                "turns": effect.turns,
                "deltas": effect.deltas,
                "multipliers": effect.multipliers,
            },
        )

    async def maybe_inflict_dot(
        self, attacker: Stats, damage: int, turns: Optional[int] = None
    ) -> None:
        """Attempt to apply one or more DoT stacks based on effect hit rate.

        The attacker's ``effect_hit_rate`` is processed in 100% chunks. Each
        iteration subtracts the target's ``effect_resistance`` and rolls for a
        stack using the remaining chance. Additional stacks are only attempted
        after a successful roll. There is always a 1% chance for the first
        stack even when resistance exceeds the hit rate.
        """

        remaining = attacker.effect_hit_rate
        resistance = self.stats.effect_resistance
        attempted = False
        while remaining > 0 or not attempted:
            effective = remaining - resistance
            if effective <= 0.0:
                if attempted:
                    break
                chance = 0.01
            else:
                chance = min(effective, 1.0)

            attempted = True
            roll = random.random()
            if roll >= chance:
                from autofighter.stats import BUS

                dtype = getattr(attacker, "damage_type", None)
                effect_name: str | None = None
                effect_id: str | None = None
                predicted_damage: int | None = None
                predicted_turns: int | None = None
                preview = None
                try:
                    if dtype is None:
                        preview = None
                    elif isinstance(dtype, str):
                        from plugins import damage_effects

                        preview = damage_effects.create_dot(dtype, damage, attacker)
                    else:
                        preview = dtype.create_dot(damage, attacker)
                except Exception:
                    preview = None

                if preview is not None:
                    effect_name = getattr(preview, "name", None)
                    effect_id = getattr(preview, "id", None)
                    predicted_damage = getattr(preview, "damage", None)
                    predicted_turns = getattr(preview, "turns", None)

                if effect_name is None:
                    effect_name = getattr(dtype, "id", None) or "dot"

                details = {
                    "effect_type": "dot",
                    "target_id": getattr(self.stats, "id", None),
                    "source_id": getattr(attacker, "id", None),
                    "damage_type": getattr(dtype, "id", dtype),
                    "chance": chance,
                    "roll": roll,
                    "resistance": resistance,
                    "remaining_hit_rate": remaining,
                }
                if effect_id:
                    details["effect_id"] = effect_id
                if predicted_damage is not None:
                    details["predicted_damage"] = predicted_damage
                if predicted_turns is not None:
                    details["predicted_turns"] = predicted_turns

                await BUS.emit_batched_async(
                    "effect_resisted",
                    effect_name,
                    self.stats,
                    attacker,
                    details,
                )
                break

            dot = attacker.damage_type.create_dot(damage, attacker)
            if dot is None:
                break

            if turns is not None:
                dot.turns = turns

            await self.add_dot(dot)
            remaining -= 1.0

    async def tick(self, others: Optional["EffectManager"] = None) -> None:
        try:
            from autofighter.rooms.battle.pacing import YIELD_MULTIPLIER
            from autofighter.rooms.battle.pacing import pace_sleep
        except (ImportError, ModuleNotFoundError):
            YIELD_MULTIPLIER = 0.0

            async def pace_sleep(_multiplier: float = 1.0) -> None:
                await asyncio.sleep(0)

        from autofighter.stats import BUS

        async def prune_hots_on_death() -> None:
            if self.stats.hp > 0 or not self.hots:
                return

            removed_hots = list(self.hots)
            self.hots.clear()
            if hasattr(self.stats, "hots"):
                self.stats.hots.clear()

            for eff in removed_hots:
                await BUS.emit_async(
                    "effect_expired",
                    eff.name,
                    self.stats,
                    {
                        "effect_type": "hot",
                        "effect_id": eff.id,
                        "expired_naturally": False,
                    },
                )

        await prune_hots_on_death()

        phase_definitions = (
            ("hot", self.hots, self.stats.hots),
            ("dot", self.dots, self.stats.dots),
        )

        def resolve_effect_name(effect: object) -> str:
            name = getattr(effect, "name", None)
            if name:
                return str(name)

            identifier = getattr(effect, "id", None)
            if identifier is None:
                return ""

            return str(identifier)

        for order, (phase_name, collection, names) in enumerate(phase_definitions):
            expired: list[object] = []
            effect_count = len(collection)
            phase_label = "HoT" if phase_name == "hot" else "DoT"
            color = "green" if phase_name == "hot" else "light_red"
            effect_ids = [str(effect_id) for effect_id in names]
            effect_names = [resolve_effect_name(eff) for eff in collection]
            phase_payload = {
                "phase": phase_name,
                "effect_count": effect_count,
                "expired_count": 0,
                "has_effects": effect_count > 0,
                "order": order,
                "target_id": getattr(self.stats, "id", None),
                "effect_ids": effect_ids,
                "effect_names": effect_names,
            }

            # Announce phase start so the frontend can render pacing beats
            start_phase_payload = phase_payload.copy()
            start_phase_payload["effect_ids"] = list(effect_ids)
            start_phase_payload["effect_names"] = list(effect_names)

            await BUS.emit_async(
                "status_phase_start",
                phase_name,
                self.stats,
                start_phase_payload,
            )

            # Batch logging for performance when many effects are present
            if self._debug and effect_count > 10:
                asyncio.create_task(
                    self._log(
                        f"[{color}]{self.stats.id} processing {effect_count} {phase_label} effects[/]"
                    )
                )

            # Process effects in parallel for better async performance when many are present
            if effect_count > 20:
                # Parallel processing for large collections
                async def tick_effect(eff):
                    if self._debug and effect_count <= 10:
                        asyncio.create_task(
                            self._log(f"[{color}]{self.stats.id} {eff.name} tick[/]")
                        )
                    return await eff.tick(self.stats), eff

                # Process in batches to avoid overwhelming the event loop
                batch_size = 50
                for i in range(0, effect_count, batch_size):
                    batch = collection[i:i + batch_size]
                    results = await asyncio.gather(*[tick_effect(eff) for eff in batch])
                    for still_active, eff in results:
                        if not still_active:
                            expired.append(eff)
                    # Early termination: if target dies, stop processing remaining effects
                    if self.stats.hp <= 0:
                        break
            else:
                # Sequential processing for smaller collections
                for eff in collection:
                    # Only log individual effects if there are few of them
                    if self._debug and effect_count <= 10:
                        asyncio.create_task(
                            self._log(f"[{color}]{self.stats.id} {eff.name} tick[/]")
                        )
                    if not await eff.tick(self.stats):
                        expired.append(eff)
                    # Early termination: if target dies, stop processing remaining effects
                    if self.stats.hp <= 0:
                        break

            for eff in expired:
                # Emit effect expired event - async for better performance
                await BUS.emit_async(
                    "effect_expired",
                    eff.name,
                    self.stats,
                    {
                        "effect_type": "hot" if isinstance(eff, HealingOverTime) else "dot",
                        "effect_id": eff.id,
                        "expired_naturally": True,
                    },
                )

                collection.remove(eff)
                if eff.id in names:
                    names.remove(eff.id)

            phase_payload.update(
                {
                    "effect_count": len(collection),
                    "expired_count": len(expired),
                    "has_effects": len(collection) > 0,
                    "effect_ids": [str(effect_id) for effect_id in names],
                    "effect_names": [resolve_effect_name(eff) for eff in collection],
                }
            )

            end_phase_payload = phase_payload.copy()
            end_phase_payload["effect_ids"] = list(phase_payload["effect_ids"])
            end_phase_payload["effect_names"] = list(phase_payload["effect_names"])

            await BUS.emit_async(
                "status_phase_end",
                phase_name,
                self.stats,
                end_phase_payload,
            )

            await pace_sleep(YIELD_MULTIPLIER)

        await prune_hots_on_death()

        # Enhanced stat modifier processing with parallelization
        mod_order = len(phase_definitions)
        expired_mods: list[StatModifier] = []

        mod_phase_payload = {
            "phase": "stat_mods",
            "effect_count": len(self.mods),
            "expired_count": 0,
            "has_effects": len(self.mods) > 0,
            "order": mod_order,
            "target_id": getattr(self.stats, "id", None),
            "effect_ids": list(self.stats.mods),
        }

        start_mod_payload = mod_phase_payload.copy()
        start_mod_payload["effect_ids"] = list(mod_phase_payload["effect_ids"])

        await BUS.emit_async(
            "status_phase_start",
            "stat_mods",
            self.stats,
            start_mod_payload,
        )

        # Batch logging for performance when many stat modifiers are present
        if self._debug and len(self.mods) > 10:
            asyncio.create_task(
                self._log(
                    f"[yellow]{self.stats.id} processing {len(self.mods)} stat modifiers[/]"
                )
            )

        # Choose processing strategy based on number of modifiers
        if len(self.mods) > 15:
            # Parallel processing for large numbers of stat modifiers
            async def tick_modifier(mod):
                if self._debug and len(self.mods) <= 10:
                    asyncio.create_task(
                        self._log(f"[yellow]{self.stats.id} {mod.name} tick[/]")
                    )
                return mod.tick(), mod

            # Process in batches to avoid overwhelming the event loop
            batch_size = 30
            for i in range(0, len(self.mods), batch_size):
                batch = self.mods[i:i + batch_size]
                results = await asyncio.gather(*[tick_modifier(mod) for mod in batch])
                for still_active, mod in results:
                    if not still_active:
                        expired_mods.append(mod)
                # Early termination: if character dies, stop processing remaining modifiers
                if self.stats.hp <= 0:
                    break
        else:
            # Sequential processing for smaller numbers of modifiers
            for mod in self.mods:
                if self._debug and len(self.mods) <= 10:
                    asyncio.create_task(
                        self._log(f"[yellow]{self.stats.id} {mod.name} tick[/]")
                    )
                if not mod.tick():
                    expired_mods.append(mod)
                # Early termination: if character dies, stop processing
                if self.stats.hp <= 0:
                    break

        # Clean up expired modifiers
        for mod in expired_mods:
            # Emit effect expired event for stat modifiers - async for better performance
            await BUS.emit_async("effect_expired", mod.name, self.stats, {
                "effect_type": "stat_modifier",
                "effect_id": mod.id,
                "expired_naturally": True
            })

            if mod in self.mods:
                self.mods.remove(mod)
                if mod.id in self.stats.mods:
                    self.stats.mods.remove(mod.id)

        mod_phase_payload.update(
            {
                "effect_count": len(self.mods),
                "expired_count": len(expired_mods),
                "has_effects": len(self.mods) > 0,
                "effect_ids": list(self.stats.mods),
            }
        )

        end_mod_payload = mod_phase_payload.copy()
        end_mod_payload["effect_ids"] = list(mod_phase_payload["effect_ids"])

        await BUS.emit_async(
            "status_phase_end",
            "stat_mods",
            self.stats,
            end_mod_payload,
        )

        await pace_sleep(YIELD_MULTIPLIER)

        # Process passive abilities if available
        await self._tick_passives(others, order=mod_order + 1)

        await pace_sleep(YIELD_MULTIPLIER)

    async def _tick_passives(
        self,
        others: Optional["EffectManager"] = None,
        *,
        order: int = 0,
    ) -> None:
        """
        Enhanced passive processing with parallelization when beneficial.
        Integrates passive ability processing into the effect manager for better performance.
        """
        from collections import Counter

        from autofighter.passives import discover
        from autofighter.stats import BUS

        if not hasattr(self.stats, 'passives'):
            passives: list[str] = []
        else:
            passives = self.stats.passives or []

        # Get passive counts and registry
        counts = Counter(passives)
        registry = discover()

        # Filter to only turn-based passives that need tick processing
        tick_passives: list[tuple[str, type[object]]] = []
        effect_ids: list[str] = []
        for pid, count in counts.items():
            cls = registry.get(pid)
            if cls is None:
                continue
            # Check if passive has any tick-related methods
            if hasattr(cls, 'on_turn_end') or hasattr(cls, 'tick') or getattr(cls, 'trigger', None) == 'turn_end':
                stacks = min(count, getattr(cls, 'max_stacks', count))
                for _ in range(stacks):
                    tick_passives.append((pid, cls))
                    effect_ids.append(pid)

        phase_payload = {
            "phase": "passives",
            "effect_count": len(tick_passives),
            "expired_count": 0,
            "has_effects": len(tick_passives) > 0,
            "order": order,
            "target_id": getattr(self.stats, "id", None),
            "effect_ids": effect_ids,
        }

        start_payload = phase_payload.copy()
        start_payload["effect_ids"] = list(effect_ids)

        await BUS.emit_async(
            "status_phase_start",
            "passives",
            self.stats,
            start_payload,
        )

        if not tick_passives:
            end_payload = phase_payload.copy()
            end_payload["effect_ids"] = list(effect_ids)
            await BUS.emit_async(
                "status_phase_end",
                "passives",
                self.stats,
                end_payload,
            )
            return

        # Batch logging for performance when many passives need processing
        if self._debug and len(tick_passives) > 10:
            asyncio.create_task(
                self._log(
                    f"[blue]{self.stats.id} processing {len(tick_passives)} passive abilities[/]"
                )
            )

        # Choose processing strategy based on number of passives
        if len(tick_passives) > 15:
            # Parallel processing for large numbers of passives
            async def process_passive(passive_data):
                pid, cls = passive_data
                if self._debug and len(tick_passives) <= 10:
                    asyncio.create_task(
                        self._log(f"[blue]{self.stats.id} {pid} passive tick[/]")
                    )

                passive_instance = cls()
                # Try turn end processing first
                if hasattr(passive_instance, 'on_turn_end'):
                    await passive_instance.on_turn_end(self.stats)
                # Fall back to tick method if available
                elif hasattr(passive_instance, 'tick'):
                    await passive_instance.tick(self.stats)
                # Fall back to general apply for turn_end triggers
                elif getattr(cls, 'trigger', None) == 'turn_end':
                    try:
                        await passive_instance.apply(self.stats)
                    except TypeError:
                        # Handle passives that don't accept extra args
                        pass

                return True  # Passives don't expire from ticking

            # Process in batches to avoid overwhelming the event loop
            batch_size = 20
            for i in range(0, len(tick_passives), batch_size):
                batch = tick_passives[i:i + batch_size]
                await asyncio.gather(*[process_passive(passive_data) for passive_data in batch])
                # Early termination: if character dies, stop processing
                if self.stats.hp <= 0:
                    break
        else:
            # Sequential processing for smaller numbers of passives
            for pid, cls in tick_passives:
                if self._debug and len(tick_passives) <= 10:
                    asyncio.create_task(
                        self._log(f"[blue]{self.stats.id} {pid} passive tick[/]")
                    )

                passive_instance = cls()
                # Try turn end processing first
                if hasattr(passive_instance, 'on_turn_end'):
                    await passive_instance.on_turn_end(self.stats)
                # Fall back to tick method if available
                elif hasattr(passive_instance, 'tick'):
                    await passive_instance.tick(self.stats)
                # Fall back to general apply for turn_end triggers
                elif getattr(cls, 'trigger', None) == 'turn_end':
                    try:
                        await passive_instance.apply(self.stats)
                    except TypeError:
                        # Handle passives that don't accept extra args
                        pass

                # Early termination: if character dies, stop processing
                if self.stats.hp <= 0:
                    break
        end_payload = phase_payload.copy()
        end_payload["effect_ids"] = list(effect_ids)

        await BUS.emit_async(
            "status_phase_end",
            "passives",
            self.stats,
            end_payload,
        )

        if self.stats.hp <= 0 and others is not None:
            for eff in list(self.dots):
                on_death = getattr(eff, "on_death", None)
                if callable(on_death):
                    result = on_death(others)
                    if hasattr(result, "__await"):
                        await result

    async def on_action(self) -> bool:
        """Run any per-action hooks on attached effects.

        Returns ``False`` if any effect cancels the action.
        """

        for eff in list(self.dots) + list(self.hots):
            handler = getattr(eff, "on_action", None)
            if callable(handler):
                if self._debug:
                    asyncio.create_task(
                        self._log(f"{self.stats.id} {eff.name} action")
                    )
                result = handler(self.stats)
                if hasattr(result, "__await"):
                    result = await result
                if result is False:
                    return False
        return True

    async def cleanup(self, target: Stats | None = None) -> None:
        """Clear remaining effects and detach status names from the stats.

        Battle resolution calls this to ensure we don't leak stacked effects
        into post-battle state snapshots.
        """
        # Proactively remove any remaining stat modifiers from the Stats object
        # so underlying StatEffects do not persist across battles.
        try:
            for mod in list(self.mods):
                try:
                    mod.remove()
                except Exception:
                    pass
        finally:
            # Remove references to effect instances
            self.dots.clear()
            self.hots.clear()
            self.mods.clear()
            # Clear status name lists on the stats object
            try:
                self.stats.dots = []
                self.stats.hots = []
                self.stats.mods = []
            except Exception:
                pass
