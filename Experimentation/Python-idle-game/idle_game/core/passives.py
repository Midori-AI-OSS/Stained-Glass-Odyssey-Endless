"""Passive ability system for persistent character abilities.

Provides passive ability management with event-based triggers.
"""

from collections import Counter
import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

log = logging.getLogger(__name__)


def _supports_event(cls: type, event: str) -> bool:
    """Return True if the passive class declares support for the event."""
    trigger = getattr(cls, "trigger", None)
    if isinstance(trigger, (list, tuple, set)):
        return event in trigger
    return trigger == event


class PassiveRegistry:
    """Registry for passive abilities with event-based triggers."""

    def __init__(self) -> None:
        self._registry: Dict[str, type] = {}

    def register(self, passive_id: str, passive_class: type) -> None:
        """Register a passive class by ID."""
        self._registry[passive_id] = passive_class

    def get_passive(self, passive_id: str) -> Optional[type]:
        """Get a passive class by ID."""
        return self._registry.get(passive_id)

    def all_passives(self) -> Dict[str, type]:
        """Get all registered passive classes."""
        return dict(self._registry)

    def trigger(self, event: str, owner: Any, **kwargs: Any) -> None:
        """Trigger passives for a given event with optional context.

        Args:
            event: Event name (e.g., 'battle_start', 'turn_start', 'hit_landed')
            owner: Entity that owns the passives
            **kwargs: Additional context for the event
        """
        if event == "battle_start" and hasattr(owner, "_recalculate_passive_aggro"):
            owner._recalculate_passive_aggro()

        counts = Counter(getattr(owner, "passives", []))
        for pid, count in counts.items():
            cls = self._registry.get(pid)
            if cls is None or not _supports_event(cls, event):
                continue

            stacks = min(count, getattr(cls, "max_stacks", count))
            for stack_idx in range(stacks):
                passive_instance = cls()
                try:
                    passive_instance.apply(owner, stack_index=stack_idx, event=event, **kwargs)
                except TypeError:
                    try:
                        passive_instance.apply(owner, stack_index=stack_idx)
                    except TypeError:
                        passive_instance.apply(owner)

                # Call event-specific handler if available
                if event == "action_taken" and hasattr(passive_instance, "on_action_taken"):
                    try:
                        passive_instance.on_action_taken(owner, **kwargs)
                    except TypeError:
                        passive_instance.on_action_taken(owner)

    def trigger_damage_taken(
        self,
        target: Any,
        attacker: Optional[Any] = None,
        damage: int = 0
    ) -> None:
        """Trigger passives specifically for damage taken events."""
        attacker_obj = attacker if attacker is not target else None
        counts = Counter(getattr(target, "passives", []))

        for pid, count in counts.items():
            cls = self._registry.get(pid)
            if cls is None:
                continue

            passive_instance = cls()

            # Check for on_damage_taken method
            if hasattr(passive_instance, "on_damage_taken"):
                stacks = min(count, getattr(cls, "max_stacks", count))
                for _ in range(stacks):
                    passive_instance.on_damage_taken(target, attacker_obj, damage)

            # Also trigger passives with explicit damage_taken trigger
            if _supports_event(cls, "damage_taken"):
                stacks = min(count, getattr(cls, "max_stacks", count))
                for _ in range(stacks):
                    try:
                        passive_instance.apply(target, attacker=attacker_obj, damage=damage, event="damage_taken")
                    except TypeError:
                        try:
                            passive_instance.apply(target, attacker=attacker_obj, damage=damage)
                        except TypeError:
                            passive_instance.apply(target)

    def trigger_turn_end(self, target: Any) -> None:
        """Trigger turn end events for passives."""
        counts = Counter(getattr(target, "passives", []))
        for pid, count in counts.items():
            cls = self._registry.get(pid)
            if cls is None:
                continue

            passive_instance = cls()

            if hasattr(passive_instance, "on_turn_end"):
                stacks = min(count, getattr(cls, "max_stacks", count))
                for _ in range(stacks):
                    passive_instance.on_turn_end(target)

    def trigger_defeat(self, target: Any) -> None:
        """Trigger defeat events for passives."""
        counts = Counter(getattr(target, "passives", []))
        for pid, count in counts.items():
            cls = self._registry.get(pid)
            if cls is None:
                continue

            passive_instance = cls()

            if hasattr(passive_instance, "on_defeat"):
                stacks = min(count, getattr(cls, "max_stacks", count))
                for _ in range(stacks):
                    passive_instance.on_defeat(target)

    def trigger_summon_defeat(self, target: Any, **kwargs: Any) -> None:
        """Trigger summon defeat events for relevant passives."""
        counts = Counter(getattr(target, "passives", []))
        for pid, count in counts.items():
            cls = self._registry.get(pid)
            if cls is None:
                continue

            passive_instance = cls()
            if hasattr(passive_instance, "on_summon_defeat"):
                stacks = min(count, getattr(cls, "max_stacks", count))
                for _ in range(stacks):
                    try:
                        passive_instance.on_summon_defeat(target, **kwargs)
                    except TypeError:
                        passive_instance.on_summon_defeat(target)

    def trigger_hit_landed(
        self,
        attacker: Any,
        target: Any,
        damage: int = 0,
        action_type: str = "attack",
        **kwargs: Any
    ) -> None:
        """Trigger passives when a hit successfully lands."""
        counts = Counter(getattr(attacker, "passives", []))
        for pid, count in counts.items():
            cls = self._registry.get(pid)
            if cls is None or not _supports_event(cls, "hit_landed"):
                continue

            passive_instance = cls()

            if hasattr(passive_instance, "on_hit_landed"):
                stacks = min(count, getattr(cls, "max_stacks", count))
                for _ in range(stacks):
                    passive_instance.on_hit_landed(attacker, target, damage, action_type, **kwargs)

            # Regular passive application
            stacks = min(count, getattr(cls, "max_stacks", count))
            for _ in range(stacks):
                try:
                    passive_instance.apply(
                        attacker,
                        hit_target=target,
                        damage=damage,
                        action_type=action_type,
                        event="hit_landed",
                        **kwargs
                    )
                except TypeError:
                    try:
                        passive_instance.apply(
                            attacker,
                            hit_target=target,
                            damage=damage,
                            action_type=action_type
                        )
                    except TypeError:
                        passive_instance.apply(attacker)

    def trigger_turn_start(self, target: Any, **kwargs: Any) -> None:
        """Trigger turn start events for passives."""
        counts = Counter(getattr(target, "passives", []))
        for pid, count in counts.items():
            cls = self._registry.get(pid)
            if cls is None:
                continue

            passive_instance = cls()
            supports_turn_start = _supports_event(cls, "turn_start")

            if not supports_turn_start and not hasattr(passive_instance, "on_turn_start"):
                continue

            if hasattr(passive_instance, "on_turn_start"):
                stacks = min(count, getattr(cls, "max_stacks", count))
                for _ in range(stacks):
                    passive_instance.on_turn_start(target, **kwargs)

            if supports_turn_start:
                stacks = min(count, getattr(cls, "max_stacks", count))
                for _ in range(stacks):
                    try:
                        passive_instance.apply(target, event="turn_start", **kwargs)
                    except TypeError:
                        try:
                            passive_instance.apply(target, **kwargs)
                        except TypeError:
                            passive_instance.apply(target)

    def trigger_level_up(self, target: Any, **kwargs: Any) -> None:
        """Trigger level up events for passives."""
        counts = Counter(getattr(target, "passives", []))
        for pid, count in counts.items():
            cls = self._registry.get(pid)
            if cls is None or not _supports_event(cls, "level_up"):
                continue

            passive_instance = cls()

            if hasattr(passive_instance, "on_level_up"):
                stacks = min(count, getattr(cls, "max_stacks", count))
                for _ in range(stacks):
                    passive_instance.on_level_up(target, **kwargs)

            stacks = min(count, getattr(cls, "max_stacks", count))
            for _ in range(stacks):
                try:
                    passive_instance.apply(target, event="level_up", **kwargs)
                except TypeError:
                    try:
                        passive_instance.apply(target, **kwargs)
                    except TypeError:
                        try:
                            passive_instance.apply(target)
                        except TypeError:
                            log.warning("Passive %s incompatible with level_up kwargs", pid)

    def describe(self, target: Any) -> List[Dict[str, Any]]:
        """Return structured information for a target's passives."""
        info: List[Dict[str, Any]] = []
        counts = Counter(getattr(target, "passives", []))

        for pid, count in counts.items():
            cls = self._registry.get(pid)
            if cls is None:
                info.append({
                    "id": pid,
                    "name": pid,
                    "stacks": count,
                    "max_stacks": None,
                    "display": "spinner",
                })
                continue

            stacks = count
            if hasattr(cls, "get_stacks"):
                try:
                    stacks = cls.get_stacks(target)
                except Exception:
                    stacks = count

            max_stacks = getattr(cls, "max_stacks", None)
            display = getattr(cls, "stack_display", None)

            if hasattr(cls, "get_display"):
                try:
                    display = cls.get_display(target)
                except Exception:
                    pass

            if display is None:
                if max_stacks == 1:
                    display = "spinner"
                elif max_stacks is None or max_stacks <= 5:
                    display = "pips"
                else:
                    display = "number"

            info.append({
                "id": pid,
                "name": getattr(cls, "name", pid),
                "stacks": stacks,
                "max_stacks": max_stacks,
                "display": display,
            })

        return info


def resolve_passives_for_rank(base_passive_id: str, rank: str, registry: PassiveRegistry) -> List[str]:
    """Resolve passive IDs based on foe rank, stacking all applicable tier variants.

    Maps base passive IDs to tier-specific variants based on the foe's rank.
    When multiple tier tags are present, ALL matching tier variants are included (stacking).

    Args:
        base_passive_id: The base passive ID (e.g., "luna_lunar_reservoir")
        rank: The foe's rank (e.g., "normal", "boss", "glitched", "prime")
        registry: PassiveRegistry to check for variant existence

    Returns:
        List of passive IDs to apply
    """
    rank_lower = rank.lower() if rank else ""
    tier_passives = []

    # Check each tier in order and add if variant exists
    if "glitched" in rank_lower:
        tier_id = f"{base_passive_id}_glitched"
        if registry.get_passive(tier_id) is not None:
            tier_passives.append(tier_id)

    if "prime" in rank_lower:
        tier_id = f"{base_passive_id}_prime"
        if registry.get_passive(tier_id) is not None:
            tier_passives.append(tier_id)

    if "boss" in rank_lower:
        tier_id = f"{base_passive_id}_boss"
        if registry.get_passive(tier_id) is not None:
            tier_passives.append(tier_id)

    return tier_passives if tier_passives else [base_passive_id]


def apply_rank_passives(foe: Any, registry: PassiveRegistry) -> None:
    """Apply rank-specific passive transformations to a foe.

    Replaces base passive IDs with tier-specific variants based on the foe's rank.
    Modifies the foe's passives list in place.

    Args:
        foe: The foe instance with rank and passives attributes
        registry: PassiveRegistry to use for resolution
    """
    if not hasattr(foe, "passives") or not hasattr(foe, "rank"):
        return

    rank = getattr(foe, "rank", "normal")
    passives = getattr(foe, "passives", [])

    if not passives:
        return

    resolved_passives = []
    for pid in passives:
        resolved_passives.extend(resolve_passives_for_rank(pid, rank, registry))

    foe.passives = resolved_passives
