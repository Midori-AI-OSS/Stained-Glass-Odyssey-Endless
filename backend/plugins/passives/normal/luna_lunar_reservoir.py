from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import ClassVar

from autofighter.stat_effect import StatEffect
from autofighter.stats import BUS

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class LunaLunarReservoir:
    """Luna's Lunar Reservoir passive - charge-based system that scales attack count."""
    plugin_type = "passive"
    id = "luna_lunar_reservoir"
    name = "Lunar Reservoir"
    trigger = ["action_taken", "ultimate_used"]  # Respond to actions and ultimates
    max_stacks = 2000  # Show charge level 0-2000
    stack_display = "number"

    # Class-level tracking of charge points for each entity
    _charge_points: ClassVar[dict[int, int]] = {}
    _events_registered: ClassVar[bool] = False
    _swords_by_owner: ClassVar[dict[int, set[int]]] = {}

    @classmethod
    def _ensure_event_hooks(cls) -> None:
        if cls._events_registered:
            return
        BUS.subscribe("luna_sword_hit", cls._on_sword_hit)
        BUS.subscribe("summon_removed", cls._handle_summon_removed)
        cls._events_registered = True

    @classmethod
    def _is_glitched_nonboss(cls, target: "Stats") -> bool:
        rank = str(getattr(target, "rank", ""))
        if not rank:
            return False
        lowered = rank.lower()
        return "glitched" in lowered and "boss" not in lowered

    @classmethod
    def _charge_multiplier(cls, charge_holder: "Stats") -> int:
        return 2 if cls._is_glitched_nonboss(charge_holder) else 1

    @classmethod
    def _resolve_charge_holder(cls, target: "Stats") -> "Stats":
        owner_attr = getattr(target, "luna_sword_owner", None)
        if owner_attr is not None:
            return owner_attr
        return target

    @classmethod
    def _ensure_charge_slot(cls, target: "Stats") -> int:
        holder = cls._resolve_charge_holder(target)
        holder_id = id(holder)
        cls._charge_points.setdefault(holder_id, 0)
        return holder_id

    @classmethod
    def register_sword(
        cls,
        owner: "Stats",
        sword: "Stats",
        label: str | None = None,
    ) -> None:
        cls._ensure_event_hooks()
        cls._ensure_charge_slot(owner)
        owner_id = id(owner)
        sword_id = id(sword)
        cls._swords_by_owner.setdefault(owner_id, set()).add(sword_id)
        if label is not None:
            setattr(sword, "luna_sword_label", label)

    @classmethod
    def unregister_sword(cls, sword: "Stats") -> None:
        sword_id = id(sword)
        owner = getattr(sword, "luna_sword_owner", None)
        owner_id = id(owner) if owner is not None else None
        swords = cls._swords_by_owner.get(owner_id)
        if not swords:
            return
        swords.discard(sword_id)
        if not swords:
            cls._swords_by_owner.pop(owner_id, None)

    @classmethod
    async def _on_sword_hit(
        cls,
        owner: "Stats | None",
        sword: "Stats",
        _target,
        amount: int,
        action_type: str,
        metadata: dict | None = None,
    ) -> None:
        actual_owner = owner
        handled = False
        if owner is not None:
            label = None
            if metadata and isinstance(metadata, dict):
                label = metadata.get("sword_label")
                handled = bool(metadata.get("charge_handled"))
            cls.register_sword(owner, sword, label if isinstance(label, str) else None)
            actual_owner = owner
        elif getattr(sword, "luna_sword_owner", None) is not None:
            actual_owner = getattr(sword, "luna_sword_owner")
        if actual_owner is None:
            return
        cls._ensure_charge_slot(actual_owner)
        rank = str(getattr(actual_owner, "rank", ""))
        per_hit = 8 if "glitched" in rank.lower() else 4
        if not handled:
            cls.add_charge(actual_owner, per_hit)
        helper = getattr(actual_owner, "_luna_sword_helper", None)
        try:
            if helper is not None and hasattr(helper, "sync_actions_per_turn"):
                helper.sync_actions_per_turn()
        except Exception:
            pass

    @classmethod
    def _handle_summon_removed(cls, summon: "Stats | None", *_: object) -> None:
        if summon is None:
            return
        cls.unregister_sword(summon)

    @classmethod
    def _apply_actions(cls, charge_target: "Stats", current_charge: int) -> None:
        """Update action cadence and dodge bonuses based on charge."""

        if current_charge < 350:
            charge_target.actions_per_turn = 2
        elif current_charge < 500:
            charge_target.actions_per_turn = 4
        elif current_charge < 700:
            charge_target.actions_per_turn = 8
        elif current_charge < 850:
            charge_target.actions_per_turn = 16
        else:  # 850+ charge
            charge_target.actions_per_turn = 32

        if current_charge > 2000:
            stacks_past_soft_cap = current_charge - 2000
            dodge_bonus = stacks_past_soft_cap * 0.00025  # 0.025% per stack

            dodge_effect = StatEffect(
                name=f"{cls.id}_dodge_bonus",
                stat_modifiers={"dodge_odds": dodge_bonus},
                duration=-1,
                source=cls.id,
            )
            charge_target.add_effect(dodge_effect)

    @classmethod
    def sync_actions(cls, target: "Stats") -> None:
        """Recompute the owner's actions per turn using current charge."""

        charge_target = cls._resolve_charge_holder(target)
        entity_id = cls._ensure_charge_slot(charge_target)
        current_charge = cls._charge_points.get(entity_id, 0)
        cls._apply_actions(charge_target, current_charge)

    async def apply(self, target: "Stats", event: str = "action_taken", **_: object) -> None:
        """Apply charge mechanics for Luna.

        Args:
            target: Entity gaining charge.
            event: Triggering event name.
        """

        cls = type(self)
        cls._ensure_event_hooks()
        charge_target = cls._resolve_charge_holder(target)
        entity_id = cls._ensure_charge_slot(charge_target)

        multiplier = cls._charge_multiplier(charge_target)

        if event == "ultimate_used":
            cls._charge_points[entity_id] += 64 * multiplier
        else:
            cls._charge_points[entity_id] += 1 * multiplier

        current_charge = cls._charge_points[entity_id]
        cls._apply_actions(charge_target, current_charge)

    async def on_turn_end(self, target: "Stats") -> None:
        """Handle charge spending at end of turn when in boosted mode."""
        holder = type(self)._resolve_charge_holder(target)
        entity_id = id(holder)

        if entity_id not in self._charge_points:
            return

        current_charge = self._charge_points[entity_id]

        # Spend 500 charge per turn when above 2000 (boosted mode)
        if current_charge > 2000:
            self._charge_points[entity_id] = max(2000, current_charge - 500)

    @classmethod
    def get_charge(cls, target: "Stats") -> int:
        """Get current charge points for an entity."""
        holder = cls._resolve_charge_holder(target)
        return cls._charge_points.get(id(holder), getattr(holder, "luna_sword_charge", 0))

    @classmethod
    def add_charge(cls, target: "Stats", amount: int = 1) -> None:
        """Add charge points (for external effects)."""
        entity_id = cls._ensure_charge_slot(target)

        # Remove hard cap - allow unlimited stacking
        cls._charge_points[entity_id] += amount
        holder = cls._resolve_charge_holder(target)
        setattr(holder, "luna_sword_charge", getattr(holder, "luna_sword_charge", 0) + amount)
        cls.sync_actions(holder)

    @classmethod
    def get_stacks(cls, target: "Stats") -> int:
        """Return current charge points for UI display."""
        holder = cls._resolve_charge_holder(target)
        return cls._charge_points.get(id(holder), getattr(holder, "luna_sword_charge", 0))

    @classmethod
    def get_display(cls, target: "Stats") -> str:
        """Display a spinner when charge is full and draining."""
        return "spinner" if cls.get_charge(target) >= 2000 else "number"

    @classmethod
    def get_description(cls) -> str:
        return (
            "Gains 1 charge per action; attack count scales from 2 up to 32 at 850+ charge. "
            "Charge beyond 2000 grants 0.025% dodge per point and drains 500 charge each turn."
        )
