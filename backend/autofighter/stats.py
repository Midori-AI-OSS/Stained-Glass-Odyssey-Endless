from collections.abc import Callable
from dataclasses import dataclass
from dataclasses import field
import importlib
import logging
import random
from typing import Optional
from typing import Union
from weakref import WeakValueDictionary

from autofighter.stat_effect import StatEffect
from plugins.damage_types._base import DamageTypeBase
from plugins.damage_types.generic import Generic
from plugins.event_bus import EventBus

log = logging.getLogger(__name__)

# Global enrage percentage applied during battles.
# Set by battle rooms when enrage is active, used in damage/heal calculations.
_ENRAGE_PERCENT: float = 0.0
_BATTLE_ACTIVE: bool = False

# Starting value for action gauges.
GAUGE_START: int = 10_000


_ACTIVE_STATS: WeakValueDictionary[int, "Stats"] = WeakValueDictionary()


class _PassiveList(list):
    """List subclass that triggers passive aggro recalculation on modification."""

    def __init__(self, owner: "Stats", iterable: Optional[list[str]] = None):
        super().__init__(iterable or [])
        self._owner = owner

    def _update(self) -> None:
        """Notify owner to recalc aggro when safe.

        During deepcopy of Player/Stats instances, attributes may be set
        before runtime-only fields (like `_aggro_passives`) exist. Guard
        against triggering recalculation until the owner is fully
        initialized to avoid AttributeError.
        """
        if not hasattr(self._owner, "_recalculate_passive_aggro"):
            return
        if not hasattr(self._owner, "_aggro_passives"):
            # Owner not fully initialized yet; skip until later
            return
        try:
            self._owner._recalculate_passive_aggro()
        except Exception:
            # Never let aggro recompute break list operations
            pass

    def append(self, item):  # type: ignore[override]
        super().append(item)
        self._update()

    def extend(self, iterable):  # type: ignore[override]
        super().extend(iterable)
        self._update()

    def remove(self, item):  # type: ignore[override]
        super().remove(item)
        self._update()

    def clear(self):  # type: ignore[override]
        super().clear()
        self._update()

    def pop(self, index=-1):  # type: ignore[override]
        value = super().pop(index)
        self._update()
        return value

    def __setitem__(self, index, value):  # type: ignore[override]
        super().__setitem__(index, value)
        self._update()

    def __delitem__(self, index):  # type: ignore[override]
        super().__delitem__(index)
        self._update()


def set_enrage_percent(value: float) -> None:
    """Set global enrage percent (e.g., 0.15 for +15% damage taken, -15% healing).

    This is applied uniformly to all entities during damage/heal resolution.
    """
    global _ENRAGE_PERCENT
    try:
        _ENRAGE_PERCENT = max(float(value), 0.0)
    except Exception:
        _ENRAGE_PERCENT = 0.0


def get_enrage_percent() -> float:
    return _ENRAGE_PERCENT


def set_battle_active(active: bool) -> None:
    """Mark whether a battle is currently active.

    Used to ignore stray async damage/heal pings after battles conclude,
    preventing post-battle loops from background tasks.
    """
    global _BATTLE_ACTIVE
    try:
        _BATTLE_ACTIVE = bool(active)
    except Exception:
        _BATTLE_ACTIVE = False


def is_battle_active() -> bool:
    return _BATTLE_ACTIVE

@dataclass
class Stats:
    # Core progression stats
    hp: int = 1000
    exp: int = 0
    level: int = 1
    exp_multiplier: float = 1.0
    actions_per_turn: int = 1
    # UI hint: how to display actions indicator ("pips" or "number")
    actions_display: str = "pips"
    # UI hint: maximum pips to render when using pips style
    actions_pips_max: int = 5

    # Base stats (immutable during battle, only change on level up or permanent upgrades)
    _base_max_hp: int = field(default=1000, init=False)
    _base_atk: int = field(default=200, init=False)
    _base_defense: int = field(default=200, init=False)
    _base_crit_rate: float = field(default=0.05, init=False)
    _base_crit_damage: float = field(default=2.0, init=False)
    _base_effect_hit_rate: float = field(default=1.0, init=False)
    _base_mitigation: float = field(default=1.0, init=False)
    _base_regain: int = field(default=100, init=False)
    _base_dodge_odds: float = field(default=0.05, init=False)
    _base_effect_resistance: float = field(default=0.05, init=False)
    _base_vitality: float = field(default=1.0, init=False)
    _base_spd: int = field(default=10, init=False)

    # Damage type and other permanent attributes
    damage_type: DamageTypeBase = field(default_factory=Generic)

    # Runtime tracking stats (not affected by effects)
    action_points: int = 0
    damage_taken: int = 0
    damage_dealt: int = 0
    kills: int = 0
    last_damage_taken: int = 0
    base_aggro: float = 0.1
    aggro_modifier: float = 0.0

    # Summoning capacity
    summon_slots_permanent: int = 0
    summon_slots_temporary: int = 0

    # Action queue
    action_gauge: int = GAUGE_START
    action_value: float = 0.0
    base_action_value: float = field(default=0.0, init=False)

    # Animation timing
    animation_duration: float = 0.0
    animation_per_target: float = 0.0

    # Ultimate system
    ultimate_charge: int = 0
    ultimate_ready: bool = False

    # Overheal system (for shields from relics/cards)
    overheal_enabled: bool = field(default=False, init=False)
    shields: int = field(default=0, init=False)  # Amount of overheal/shields

    # Collections
    passives: list[str] = field(default_factory=list)
    dots: list[str] = field(default_factory=list)
    hots: list[str] = field(default_factory=list)
    mods: list[str] = field(default_factory=list)
    _aggro_passives: list[str] = field(default_factory=list, init=False)

    # Effects system
    _active_effects: list[StatEffect] = field(default_factory=list, init=False)

    level_up_gains: dict[str, float] = field(
        default_factory=lambda: {
            "max_hp": 10.0,
            "atk": 5.0,
            "defense": 3.0,
        }
    )

    def __post_init__(self):
        """Initialize base stats from constructor values."""
        # Initialize base stats with default values if not already set
        if not hasattr(self, '_base_max_hp') or self._base_max_hp == 0:
            self._base_max_hp = 1000
        if not hasattr(self, '_base_atk') or self._base_atk == 0:
            self._base_atk = 200
        if not hasattr(self, '_base_defense') or self._base_defense == 0:
            self._base_defense = 200
        if not hasattr(self, '_base_crit_rate'):
            self._base_crit_rate = 0.05
        if not hasattr(self, '_base_crit_damage'):
            self._base_crit_damage = 2.0
        _ACTIVE_STATS[id(self)] = self
        if not hasattr(self, '_base_effect_hit_rate'):
            self._base_effect_hit_rate = 1.0
        if not hasattr(self, '_base_mitigation'):
            self._base_mitigation = 1.0
        if not hasattr(self, '_base_regain'):
            self._base_regain = 100
        if not hasattr(self, '_base_dodge_odds'):
            self._base_dodge_odds = 0.05
        if not hasattr(self, '_base_effect_resistance'):
            self._base_effect_resistance = 0.05
        if not hasattr(self, '_base_vitality'):
            self._base_vitality = 1.0
        if not hasattr(self, '_base_spd'):
            self._base_spd = 10

        # Set hp to match max_hp at start
        self.hp = self.max_hp

        dt = getattr(self, "damage_type", None)
        try:
            if hasattr(dt, "apply_aggro"):
                dt.apply_aggro(self)
            else:
                self.aggro_modifier += float(getattr(dt, "aggro", 0.0))
        except Exception:
            pass

        if not isinstance(self.passives, _PassiveList):
            object.__setattr__(self, "passives", _PassiveList(self, self.passives))
        self._recalculate_passive_aggro()

    @property
    def summon_slot_capacity(self) -> int:
        """Total summon slots available, combining permanent and temporary values."""

        return max(0, int(self.summon_slots_permanent + self.summon_slots_temporary))

    def ensure_permanent_summon_slots(self, minimum: int) -> None:
        """Guarantee at least ``minimum`` permanent summon slots."""

        if minimum <= 0:
            return
        if self.summon_slots_permanent < minimum:
            self.summon_slots_permanent = minimum

    def add_permanent_summon_slots(self, amount: int = 1) -> None:
        """Increase permanent summon slots by ``amount``."""

        if amount > 0:
            self.summon_slots_permanent += amount

    def remove_permanent_summon_slots(self, amount: int = 1) -> None:
        """Reduce permanent summon slots by ``amount`` without going below zero."""

        if amount > 0:
            self.summon_slots_permanent = max(0, self.summon_slots_permanent - amount)

    def add_temporary_summon_slots(self, amount: int = 1) -> None:
        """Increase temporary summon slots by ``amount`` for the current battle."""

        if amount > 0:
            self.summon_slots_temporary += amount

    def remove_temporary_summon_slots(self, amount: int = 1) -> None:
        """Reduce temporary summon slots by ``amount`` without going below zero."""

        if amount > 0:
            self.summon_slots_temporary = max(0, self.summon_slots_temporary - amount)

    def reset_temporary_summon_slots(self) -> None:
        """Clear all temporary summon slots (typically at battle end)."""

        self.summon_slots_temporary = 0

    def __setattr__(self, name, value):
        if name == "passives" and not isinstance(value, _PassiveList):
            object.__setattr__(self, name, _PassiveList(self, value))
            if "_aggro_passives" in self.__dict__:
                self._recalculate_passive_aggro()
        else:
            object.__setattr__(self, name, value)

    # Runtime stat properties (base stats + effects)
    @property
    def max_hp(self) -> int:
        """Calculate runtime max HP (base + effects)."""
        return int(self._base_max_hp + self._calculate_stat_modifier('max_hp'))

    @property
    def atk(self) -> int:
        """Calculate runtime attack (base + effects)."""
        return int(self._base_atk + self._calculate_stat_modifier('atk'))

    @property
    def defense(self) -> int:
        """Calculate runtime defense (base + effects)."""
        return int(self._base_defense + self._calculate_stat_modifier('defense'))

    @property
    def crit_rate(self) -> float:
        """Calculate runtime crit rate (base + effects)."""
        return max(0.0, self._base_crit_rate + self._calculate_stat_modifier('crit_rate'))

    @property
    def crit_damage(self) -> float:
        """Calculate runtime crit damage (base + effects)."""
        return max(1.0, self._base_crit_damage + self._calculate_stat_modifier('crit_damage'))

    @property
    def effect_hit_rate(self) -> float:
        """Calculate runtime effect hit rate (base + effects)."""
        return max(0.0, self._base_effect_hit_rate + self._calculate_stat_modifier('effect_hit_rate'))

    @property
    def mitigation(self) -> float:
        """Calculate runtime mitigation (base + effects)."""
        return max(0.1, self._base_mitigation + self._calculate_stat_modifier('mitigation'))

    @mitigation.setter
    def mitigation(self, value: float) -> None:  # type: ignore[override]
        try:
            self._base_mitigation = float(value)
        except Exception:
            # Fallback to no-op on invalid values
            pass

    @property
    def regain(self) -> int:
        """Calculate runtime regain (base + effects)."""
        return int(max(0, self._base_regain + self._calculate_stat_modifier('regain')))

    @property
    def dodge_odds(self) -> float:
        """Calculate runtime dodge odds (base + effects)."""
        return max(0.0, min(1.0, self._base_dodge_odds + self._calculate_stat_modifier('dodge_odds')))

    @property
    def effect_resistance(self) -> float:
        """Calculate runtime effect resistance (base + effects)."""
        return max(0.0, self._base_effect_resistance + self._calculate_stat_modifier('effect_resistance'))

    @property
    def vitality(self) -> float:
        """Calculate runtime vitality (base + effects)."""
        return max(0.01, self._base_vitality + self._calculate_stat_modifier('vitality'))

    @vitality.setter
    def vitality(self, value: float) -> None:  # type: ignore[override]
        try:
            self._base_vitality = float(value)
        except Exception:
            pass

    @property
    def spd(self) -> int:
        """Calculate runtime speed (base + effects)."""
        return int(max(1, self._base_spd + self._calculate_stat_modifier('spd')))

    @spd.setter
    def spd(self, value: int) -> None:  # type: ignore[override]
        try:
            self._base_spd = int(value)
        except Exception:
            pass

    @property
    def aggro(self) -> float:
        """Calculate current aggro score."""
        defense_term = 0.0
        try:
            defense_term = (self.defense - self._base_defense) / self._base_defense
        except Exception:
            defense_term = 0.0
        modifier = (
            self.aggro_modifier
            + self._calculate_stat_modifier("aggro_modifier")
        )
        return self.base_aggro * (1 + modifier + defense_term)

    def _calculate_stat_modifier(self, stat_name: str) -> Union[int, float]:
        """Calculate the total modifier for a stat from all active effects."""
        total: float = 0.0
        for effect in self._active_effects:
            if stat_name in effect.stat_modifiers:
                total += effect.stat_modifiers[stat_name]
        return total

    # Base stat access methods (for permanent changes like leveling)
    def set_base_stat(self, stat_name: str, value: Union[int, float]) -> None:
        """Set a base stat value (use only for permanent changes like leveling)."""
        base_attr = f"_base_{stat_name}"
        if hasattr(self, base_attr):
            setattr(self, base_attr, value)
        else:
            log.warning(f"Attempted to set unknown base stat: {stat_name}")

    def get_base_stat(self, stat_name: str) -> Union[int, float]:
        """Get a base stat value."""
        base_attr = f"_base_{stat_name}"
        if hasattr(self, base_attr):
            return getattr(self, base_attr)
        return 0

    def modify_base_stat(self, stat_name: str, amount: Union[int, float]) -> None:
        """Modify a base stat (use only for permanent changes like leveling)."""
        current = self.get_base_stat(stat_name)
        self.set_base_stat(stat_name, current + amount)

    def change_damage_type(self, new_type: DamageTypeBase) -> None:
        """Change damage type and update aggro modifiers."""
        try:
            old = getattr(self, "damage_type", None)
            if old is not None:
                if hasattr(old, "remove_aggro"):
                    old.remove_aggro(self)
                else:
                    self.aggro_modifier -= float(getattr(old, "aggro", 0.0))
        except Exception:
            pass
        self.damage_type = new_type
        try:
            if hasattr(new_type, "apply_aggro"):
                new_type.apply_aggro(self)
            else:
                self.aggro_modifier += float(getattr(new_type, "aggro", 0.0))
        except Exception:
            pass

    def _recalculate_passive_aggro(self) -> None:
        # Ensure tracking container exists even during partial construction
        if not hasattr(self, "_aggro_passives"):
            object.__setattr__(self, "_aggro_passives", [])
        try:
            from autofighter.passives import discover

            registry = discover()
        except Exception:
            return

        for pid in list(self._aggro_passives):
            cls = registry.get(pid)
            if cls is None:
                continue
            instance = cls()
            try:
                if hasattr(instance, "remove_aggro"):
                    instance.remove_aggro(self)
                else:
                    self.aggro_modifier -= float(getattr(instance, "aggro", 0.0))
            except Exception:
                pass
        self._aggro_passives.clear()

        for pid in self.passives:
            cls = registry.get(pid)
            if cls is None:
                continue
            instance = cls()
            applied = False
            try:
                if hasattr(instance, "apply_aggro"):
                    instance.apply_aggro(self)
                    applied = True
                elif hasattr(instance, "aggro"):
                    self.aggro_modifier += float(getattr(instance, "aggro", 0.0))
                    applied = True
            except Exception:
                continue
            if applied:
                self._aggro_passives.append(pid)

    # Effect management methods
    def add_effect(self, effect: StatEffect) -> None:
        """Add a stat effect."""
        # Remove any existing effect with the same name to prevent stacking
        self.remove_effect_by_name(effect.name)
        self._active_effects.append(effect)
        log.debug(f"Added effect {effect.name} with modifiers {effect.stat_modifiers}")

    def remove_effect_by_name(self, effect_name: str) -> bool:
        """Remove an effect by name. Returns True if an effect was removed."""
        initial_count = len(self._active_effects)
        self._active_effects = [e for e in self._active_effects if e.name != effect_name]
        removed = len(self._active_effects) < initial_count
        if removed:
            log.debug(f"Removed effect {effect_name}")
        return removed

    def remove_effect_by_source(self, source: str) -> int:
        """Remove all effects from a specific source. Returns number of effects removed."""
        initial_count = len(self._active_effects)
        self._active_effects = [e for e in self._active_effects if e.source != source]
        removed_count = initial_count - len(self._active_effects)
        if removed_count > 0:
            log.debug(f"Removed {removed_count} effects from source {source}")
        return removed_count

    def tick_effects(self) -> None:
        """Update all temporary effects, removing expired ones."""
        expired_effects = []
        for effect in self._active_effects:
            effect.tick()
            if effect.is_expired():
                expired_effects.append(effect.name)

        for effect_name in expired_effects:
            self.remove_effect_by_name(effect_name)

    def get_active_effects(self) -> list[StatEffect]:
        """Get a copy of all active effects."""
        return self._active_effects.copy()

    def clear_all_effects(self) -> None:
        """Remove all active effects."""
        self._active_effects.clear()
        log.debug("Cleared all stat effects")

    @property
    def element_id(self) -> str:
        dt = getattr(self, "damage_type", Generic())
        if isinstance(dt, str):
            return dt
        ident = getattr(dt, "id", None) or getattr(dt, "name", None)
        return str(ident or dt)

    def exp_to_level(self) -> int:
        return (2 ** self.level) * 50

    async def maybe_regain(self, turn: int) -> None:
        if turn % 2 != 0:
            return
        bonus = max(self.regain - 100, 0) * 0.00005
        percent = 0.01 + bonus
        heal = int(self.max_hp * percent)
        await self.apply_healing(heal)

    def _on_level_up(self) -> None:
        inc = random.uniform(0.003 * self.level, 0.008 * self.level)

        # Apply percentage increase to base stats
        base_stat_names = ['max_hp', 'atk', 'defense', 'crit_rate', 'crit_damage',
                          'effect_hit_rate', 'mitigation', 'regain', 'dodge_odds',
                          'effect_resistance', 'vitality']

        for stat_name in base_stat_names:
            current_base = self.get_base_stat(stat_name)
            if isinstance(current_base, (int, float)) and current_base > 0:
                new_val = current_base * (1 + inc)
                self.set_base_stat(stat_name, new_val)

        # Apply fixed gains from level_up_gains to base stats
        for stat, base in self.level_up_gains.items():
            self.modify_base_stat(stat, base * self.level)

        # Set current HP to new max HP
        self.hp = self.max_hp

    async def _trigger_level_up_passives(self) -> None:
        """Trigger passive registry for level up events."""
        try:
            # Import locally to avoid circular imports
            from autofighter.passives import PassiveRegistry
            registry = PassiveRegistry()
            await registry.trigger_level_up(self, new_level=self.level)
        except Exception as e:
            log.warning("Error triggering level_up passives: %s", e)

    def gain_exp(self, amount: int) -> None:
        if self.level < 1000:
            amount *= 10
        self.exp += int(amount * self.exp_multiplier * self.vitality)
        while self.exp >= self.exp_to_level():
            needed = self.exp_to_level()
            self.exp -= needed
            self.level += 1
            self._on_level_up()
            # Trigger level up passives asynchronously
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self._trigger_level_up_passives())
            except Exception:
                # If no event loop is running, skip passive triggers
                pass

    def add_ultimate_charge(self, amount: int = 1) -> None:
        """Increase ultimate charge, capping at 15."""
        if self.ultimate_ready:
            return
        self.ultimate_charge = min(15, self.ultimate_charge + amount)
        if self.ultimate_charge >= 15:
            self.ultimate_ready = True

    def handle_ally_action(self, actor: "Stats") -> None:
        """Grant bonus ultimate charge when a teammate takes an action.

        Wind-aligned characters gain charge whenever another member of their
        team acts. The acting entity already gains charge from the battle loop,
        so we only grant this bonus to allies (not self) to avoid double-counting.
        """
        if actor is self:
            return
        dt = getattr(self, "damage_type", None)
        if getattr(dt, "id", "").lower() == "wind":
            self.add_ultimate_charge(actor.actions_per_turn)


    async def apply_damage(
        self,
        amount: float,
        attacker: Optional["Stats"] = None,
        *,
        trigger_on_hit: bool = True,
        action_name: Optional[str] = None,
    ) -> int:
        # Drop any stray post-battle damage tasks to avoid loops.
        from autofighter.stats import is_battle_active  # local import for clarity
        if not is_battle_active():
            return 0
        # If already dead, ignore further damage applications to avoid
        # post-death damage loops from async tasks or event subscribers.
        if getattr(self, "hp", 0) <= 0:
            return 0
        def _ensure(obj: "Stats") -> DamageTypeBase:
            dt = getattr(obj, "damage_type", Generic())
            if isinstance(dt, str):
                module = importlib.import_module(
                    f"plugins.damage_types.{dt.lower()}"
                )
                dt = getattr(module, dt)()
                obj.damage_type = dt
            return dt

        critical = False
        if attacker is not None:
            if random.random() < self.dodge_odds:
                log.info(
                    "%s dodges attack from %s",
                    self.id,
                    getattr(attacker, "id", "unknown"),
                )
                return 0
            atk_type = _ensure(attacker)
            # Avoid recursive chains from secondary effects (e.g., Lightning on-hit reactions)
            if trigger_on_hit:
                atk_type.on_hit(attacker, self)
            if random.random() < attacker.crit_rate:
                critical = True
                amount *= attacker.crit_damage
            amount = atk_type.on_damage(amount, attacker, self)
        self_type = _ensure(self)
        amount = self_type.on_damage_taken(amount, attacker, self)
        amount = self_type.on_party_damage_taken(amount, attacker, self)
        src_vit = attacker.vitality if attacker is not None else 1.0
        # Guard against division by zero if vitality/mitigation are driven to 0 by effects
        defense_term = max(self.defense ** 5, 1)
        vit = float(self.vitality) if isinstance(self.vitality, (int, float)) else 1.0
        mit = float(self.mitigation) if isinstance(self.mitigation, (int, float)) else 1.0
        # Clamp to a tiny positive epsilon to avoid zero/NaN
        EPS = 1e-6
        vit = vit if vit > EPS else EPS
        mit = mit if mit > EPS else EPS
        denom = defense_term * vit * mit
        amount = ((amount ** 2) * src_vit) / denom
        # Enrage: increase damage taken globally by N% per enrage stack
        enr = get_enrage_percent()
        if enr > 0:
            amount *= (1.0 + enr)
        amount = max(int(amount), 1)
        if critical and attacker is not None:
            log.info("Critical hit! %s -> %s for %s", attacker.id, self.id, amount)
            # Emit critical hit event for battle logging - async for better performance
            await BUS.emit_async("critical_hit", attacker, self, amount, action_name or "attack")
        original_amount = amount
        self.last_damage_taken = amount
        self.damage_taken += amount

        # Handle shields/overheal absorption first
        if self.shields > 0:
            shield_absorbed = min(amount, self.shields)
            self.shields -= shield_absorbed
            amount -= shield_absorbed
            # Emit shield absorbed event for battle logging - async for better performance
            if shield_absorbed > 0:
                await BUS.emit_async("shield_absorbed", self, shield_absorbed, "shield")

        # Apply remaining damage to HP
        old_hp = self.hp
        if amount > 0:
            self.hp = max(self.hp - amount, 0)

        post_hit_hp = self.hp

        # Emit defeat/kill events if this damage reduced HP to zero
        if old_hp > 0 and self.hp <= 0:
            if attacker is not None:
                await BUS.emit_async(
                    "entity_killed",
                    self,
                    attacker,
                    original_amount,
                    "death",
                    {"killer_id": getattr(attacker, "id", "unknown")},
                )
            await BUS.emit_async("entity_defeat", self)

        # Trigger passive registry for damage taken events
        if original_amount > 0:
            try:
                # Import locally to avoid circular imports
                from autofighter.passives import PassiveRegistry
                registry = PassiveRegistry()
                await registry.trigger_damage_taken(self, attacker, original_amount)
            except Exception as e:
                log.warning("Error triggering damage_taken passives: %s", e)

        # Use async emission for high-frequency damage events to reduce blocking
        BUS.emit_batched(
            "damage_taken",
            self,
            attacker,
            original_amount,
            old_hp,
            post_hit_hp,
        )
        if attacker is not None:
            attacker.damage_dealt += original_amount
            BUS.emit_batched("damage_dealt", attacker, self, original_amount, "attack", None, None, action_name)
        return original_amount

    async def apply_cost_damage(self, amount: int) -> int:
        """Apply self-inflicted damage that ignores mitigation and shields."""
        from autofighter.stats import is_battle_active  # local import for clarity

        if not is_battle_active():
            return 0
        if getattr(self, "hp", 0) <= 0:
            return 0
        amount = max(int(amount), 0)
        self.last_damage_taken = amount
        self.damage_taken += amount
        old_hp = self.hp
        if amount > 0:
            self.hp = max(self.hp - amount, 1)
            try:
                from autofighter.passives import PassiveRegistry

                registry = PassiveRegistry()
                await registry.trigger_damage_taken(self, None, amount)
            except Exception as e:  # pragma: no cover - defensive
                log.warning("Error triggering damage_taken passives: %s", e)
        post_hit_hp = self.hp
        BUS.emit_batched("damage_taken", self, None, amount, old_hp, post_hit_hp)
        return amount

    async def apply_healing(self, amount: int, healer: Optional["Stats"] = None, source_type: str = "heal", source_name: Optional[str] = None) -> int:
        def _ensure(obj: "Stats") -> DamageTypeBase:
            dt = getattr(obj, "damage_type", Generic())
            if isinstance(dt, str):
                module = importlib.import_module(
                    f"plugins.damage_types.{dt.lower()}"
                )
                dt = getattr(module, dt)()
                obj.damage_type = dt
            return dt

        if healer is not None:
            heal_type = _ensure(healer)
            amount = heal_type.on_heal(amount, healer, self)
        self_type = _ensure(self)
        amount = self_type.on_heal_received(amount, healer, self)
        src_vit = healer.vitality if healer is not None else 1.0
        # Healing is amplified by both source and target vitality
        amount = amount * src_vit * self.vitality
        # Enrage: reduce healing output globally by N% per enrage stack
        enr = get_enrage_percent()
        if enr > 0:
            amount *= max(1.0 - enr, 0.0)
        amount = int(amount)

        # Handle overheal/shields if enabled
        if self.overheal_enabled:
            if self.hp < self.max_hp:
                # Heal normal HP first
                normal_heal = min(amount, self.max_hp - self.hp)
                self.hp += normal_heal
                amount -= normal_heal

            # Add any remaining healing as shields with diminishing returns
            if amount > 0:
                # Calculate penalty based on CURRENT shield amount
                current_overheal_percent = (self.shields / self.max_hp) * 100

                if current_overheal_percent <= 0:
                    # No existing overheal - healing works normally
                    self.shields += amount
                else:
                    # Apply diminishing returns based on current overheal percentage
                    # At 10% overheal, healing effectiveness = 1/5 = 0.2
                    # So 10 healing gives 2 shields, matching the example
                    healing_effectiveness = 1.0 / 5.0  # 20% effectiveness when overhealed
                    shields_to_add = amount * healing_effectiveness
                    self.shields += int(shields_to_add)
        else:
            # Standard healing - cap at max HP
            self.hp = min(self.hp + amount, self.max_hp)

        # Use batched emission for high-frequency healing events
        BUS.emit_batched("heal_received", self, healer, amount)
        if healer is not None:
            BUS.emit_batched("heal", healer, self, amount, source_type, source_name)
        return amount

    def enable_overheal(self) -> None:
        """Enable overheal/shields for this entity (typically from relic/card effects)."""
        self.overheal_enabled = True

    def disable_overheal(self) -> None:
        """Disable overheal/shields and remove any existing shields."""
        self.overheal_enabled = False
        self.shields = 0

    @property
    def effective_hp(self) -> int:
        """Get total effective HP (actual HP + shields)."""
        return self.hp + self.shields


def calc_animation_time(actor: "Stats", targets: int) -> float:
    """Compute total animation wait time for an action."""

    base = getattr(actor, "animation_duration", 0.0)
    per = getattr(actor, "animation_per_target", 0.0)
    return base + per * max(targets - 1, 0)


StatusHook = Callable[["Stats"], None]
STATUS_HOOKS: list[StatusHook] = []
BUS = EventBus()


def _reset_temporary_slots_on_battle_end(*_args, **__):
    """Clear temporary summon slots for all tracked stats instances."""

    for stats in list(_ACTIVE_STATS.values()):
        stats.reset_temporary_summon_slots()


BUS.subscribe("battle_end", _reset_temporary_slots_on_battle_end)

def _log_damage_taken(
    target: "Stats", attacker: Optional["Stats"], amount: int
) -> None:
    attacker_id = getattr(attacker, "id", "unknown")
    log.info("%s takes %s from %s", target.id, amount, attacker_id)


def _log_heal_received(
    target: "Stats", healer: Optional["Stats"], amount: int
) -> None:
    healer_id = getattr(healer, "id", "unknown")
    log.info("%s heals %s from %s", target.id, amount, healer_id)


BUS.subscribe("damage_taken", _log_damage_taken)
BUS.subscribe("heal_received", _log_heal_received)


def add_status_hook(hook: StatusHook) -> None:
    STATUS_HOOKS.append(hook)


def apply_status_hooks(stats: "Stats") -> None:
    for hook in STATUS_HOOKS:
        hook(stats)


# Note: Global user-level buff application has moved to run setup/load time.
# This prevents per-battle reapplication/stacking. Other hooks may still be
# registered via add_status_hook elsewhere.
