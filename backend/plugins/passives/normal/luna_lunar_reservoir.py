from dataclasses import dataclass
from math import ceil
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
    trigger = ["action_taken", "ultimate_used", "hit_landed"]  # Respond to actions, ultimates, and hits
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
    def _rank_lower(cls, target: "Stats | None") -> str:
        if target is None:
            return ""
        rank = getattr(target, "rank", "")
        if not rank:
            return ""
        return str(rank).lower()

    @classmethod
    def _is_glitched_nonboss(cls, target: "Stats") -> bool:
        lowered = cls._rank_lower(target)
        return "glitched" in lowered and "boss" not in lowered

    @classmethod
    def _is_prime(cls, target: "Stats") -> bool:
        return "prime" in cls._rank_lower(target)

    @classmethod
    def _charge_multiplier(cls, charge_holder: "Stats") -> int:
        multiplier = 2 if cls._is_glitched_nonboss(charge_holder) else 1
        if cls._is_prime(charge_holder):
            multiplier *= 5
        return multiplier

    @classmethod
    def _sword_charge_amount(cls, owner: "Stats | None") -> int:
        if owner is None:
            return 0
        per_hit = 4
        lowered = cls._rank_lower(owner)
        if "glitched" in lowered:
            per_hit *= 2
        if "prime" in lowered:
            per_hit *= 5
        return per_hit

    @classmethod
    async def _apply_prime_healing(cls, owner: "Stats", damage: int | None) -> bool:
        if not cls._is_prime(owner):
            return False
        amount = damage or 0
        heal = ceil(amount * 0.000001)
        heal = max(1, min(32, heal))
        await owner.apply_healing(
            heal,
            healer=owner,
            source_type="passive",
            source_name=cls.id,
        )
        return True

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
        metadata_dict = metadata if isinstance(metadata, dict) else {}
        if owner is not None:
            label = metadata_dict.get("sword_label") if metadata_dict else None
            handled = bool(metadata_dict.get("charge_handled"))
            cls.register_sword(owner, sword, label if isinstance(label, str) else None)
            actual_owner = owner
        elif getattr(sword, "luna_sword_owner", None) is not None:
            actual_owner = getattr(sword, "luna_sword_owner")
        if actual_owner is None:
            return
        cls._ensure_charge_slot(actual_owner)
        per_hit = cls._sword_charge_amount(actual_owner)
        if not handled:
            cls.add_charge(actual_owner, per_hit)
        if not bool(metadata_dict.get("prime_heal_handled")):
            healed = await cls._apply_prime_healing(actual_owner, amount)
            if isinstance(metadata, dict):
                metadata["prime_heal_handled"] = True
                metadata["prime_heal_success"] = healed
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
        """Update action cadence and attack bonus based on charge."""

        setattr(charge_target, "luna_sword_charge", current_charge)

        doubles = min(current_charge // 25, 2000)
        if doubles <= 4:
            charge_target.actions_per_turn = 2 << doubles
        else:
            charge_target.actions_per_turn = 32 + (doubles - 4)

        bonus_effect_name = "luna_lunar_reservoir_atk_bonus"
        if current_charge > 2000:
            excess_charge = current_charge - 2000
            bonus_tiers = excess_charge // 100
            if bonus_tiers > 0:
                base_atk = getattr(charge_target, "_base_atk", 0)
                atk_bonus = int(base_atk * 0.55 * bonus_tiers)
                if atk_bonus:
                    atk_effect = StatEffect(
                        name=bonus_effect_name,
                        stat_modifiers={"atk": atk_bonus},
                        duration=-1,
                        source=cls.id,
                    )
                    charge_target.add_effect(atk_effect)
                    return
        charge_target.remove_effect_by_name(bonus_effect_name)

    @classmethod
    def sync_actions(cls, target: "Stats") -> None:
        """Recompute the owner's actions per turn using current charge."""

        charge_target = cls._resolve_charge_holder(target)
        entity_id = cls._ensure_charge_slot(charge_target)
        current_charge = cls._charge_points.get(entity_id, 0)
        cls._apply_actions(charge_target, current_charge)

    async def apply(self, target: "Stats", event: str = "action_taken", **kwargs: object) -> None:
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
        damage = kwargs.get("damage")
        try:
            damage_value = int(damage)
        except (TypeError, ValueError):
            damage_value = 0

        if event == "ultimate_used":
            cls._charge_points[entity_id] += 64 * multiplier
        elif event != "hit_landed":
            cls._charge_points[entity_id] += 1 * multiplier

        current_charge = cls._charge_points[entity_id]
        cls._apply_actions(charge_target, current_charge)

        if event == "hit_landed":
            await cls._apply_prime_healing(charge_target, damage_value)

    async def on_turn_end(self, target: "Stats") -> None:
        """Keep the owner's action cadence in sync at turn end."""
        holder = type(self)._resolve_charge_holder(target)
        type(self).sync_actions(holder)

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
        cls.sync_actions(holder)

    @classmethod
    def get_stacks(cls, target: "Stats") -> int:
        """Return current charge points for UI display."""
        holder = cls._resolve_charge_holder(target)
        return cls._charge_points.get(id(holder), getattr(holder, "luna_sword_charge", 0))

    @classmethod
    def get_display(cls, target: "Stats") -> str:
        """Display a spinner when charge meets or exceeds the soft cap."""
        return "spinner" if cls.get_charge(target) >= 2000 else "number"

    @classmethod
    def get_description(cls) -> str:
        return (
            "Gains 1 charge per action. Every 25 charge doubles actions per turn (capped after 2000 doublings). "
            "Stacks above 2000 grant +15% of Luna's base ATK per 100 excess charge with no automatic drain."
        )
