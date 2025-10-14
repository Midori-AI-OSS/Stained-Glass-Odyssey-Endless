from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import ClassVar
from typing import Iterable
from typing import Sequence
from weakref import ReferenceType
from weakref import ref

from autofighter.stat_effect import StatEffect
from autofighter.stats import BUS

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class RyneOracleOfBalance:
    """Ryne's Oracle of Balance passive - builds equilibrium to shield allies."""

    plugin_type = "passive"
    id = "ryne_oracle_of_balance"
    name = "Oracle of Balance"
    trigger = [
        "battle_start",
        "turn_start",
        "action_taken",
        "hit_landed",
        "ultimate_used",
    ]
    stack_display = "pips"
    max_stacks = 120  # Soft cap for display; balance can exceed this value

    SOFT_CAP: ClassVar[int] = 120
    POST_CAP_EFFICIENCY: ClassVar[float] = 0.5

    _balance_points: ClassVar[dict[int, int]] = {}
    _balance_totals: ClassVar[dict[int, int]] = {}
    _balance_carry: ClassVar[dict[int, float]] = {}
    _luna_links: ClassVar[dict[int, ReferenceType["Stats"]]] = {}
    _ally_refs: ClassVar[dict[int, list[ReferenceType["Stats"]]]] = {}
    _bus_handlers: ClassVar[dict[int, dict[str, object]]] = {}

    ACTION_GAIN: ClassVar[int] = 2
    HIT_GAIN: ClassVar[int] = 1
    ULTIMATE_GAIN: ClassVar[int] = 4
    LUNA_HIT_GAIN: ClassVar[int] = 2
    THRESHOLD: ClassVar[int] = 6

    async def apply(self, owner: "Stats", event: str | None = None, **kwargs) -> None:
        """Handle Ryne's passive triggers for the supplied *event*."""

        if event == "battle_start":
            await self._handle_battle_start(owner, **kwargs)
            return
        if event == "turn_start":
            await self._handle_turn_start(owner, **kwargs)
            return

        if event == "action_taken":
            await self._maybe_cache_party(owner, kwargs.get("party"))
            await self._add_balance(owner, self.ACTION_GAIN)
            return

        if event == "hit_landed":
            await self._add_balance(owner, self.HIT_GAIN)
            return

        if event == "ultimate_used":
            await self._add_balance(owner, self.ULTIMATE_GAIN)
            return

    @classmethod
    async def _handle_battle_start(
        cls,
        owner: "Stats",
        party: Sequence[object] | None = None,
        **_: object,
    ) -> None:
        owner_id = id(owner)
        cls._balance_points.setdefault(owner_id, 0)
        cls._balance_totals.setdefault(owner_id, 0)
        cls._balance_carry.setdefault(owner_id, 0.0)
        cls._register_bus_handlers(owner)
        await cls._maybe_cache_party(owner, party)
        cls._apply_owner_aura(owner)
        luna = cls._resolve_luna(owner_id)
        if luna is not None:
            cls._apply_link_aura(owner, luna)

    @classmethod
    async def _handle_turn_start(
        cls,
        owner: "Stats",
        party: Sequence[object] | None = None,
        **_: object,
    ) -> None:
        await cls._maybe_cache_party(owner, party)
        owner_id = id(owner)
        if owner_id not in cls._balance_points:
            cls._balance_points[owner_id] = 0

    @classmethod
    async def _add_balance(cls, owner: "Stats", amount: int) -> None:
        if amount <= 0:
            return
        owner_id = id(owner)
        current = cls._balance_points.get(owner_id, 0)
        total_before = cls._balance_totals.get(owner_id, 0)
        total_after = total_before + amount
        cls._balance_totals[owner_id] = total_after

        soft_cap = max(0, cls.SOFT_CAP)
        carry = cls._balance_carry.get(owner_id, 0.0)
        gained = 0

        if soft_cap == 0:
            gained = amount
        elif total_before >= soft_cap:
            carry += amount * cls.POST_CAP_EFFICIENCY
            rounded = int(carry)
            if rounded:
                carry -= rounded
                gained += rounded
        elif total_after <= soft_cap:
            gained = amount
        else:
            normal_gain = soft_cap - total_before
            if normal_gain > 0:
                gained += normal_gain
            overflow = amount - max(normal_gain, 0)
            if overflow > 0:
                carry += overflow * cls.POST_CAP_EFFICIENCY
                rounded = int(carry)
                if rounded:
                    carry -= rounded
                    gained += rounded

        cls._balance_carry[owner_id] = carry

        if gained <= 0:
            cls._balance_points[owner_id] = current
            return

        cls._balance_points[owner_id] = current + gained
        await cls._check_threshold(owner)

    @classmethod
    async def _check_threshold(cls, owner: "Stats") -> None:
        owner_id = id(owner)
        threshold = max(1, cls.THRESHOLD)
        current = cls._balance_points.get(owner_id, 0)
        while current >= threshold:
            current -= threshold
            cls._balance_points[owner_id] = current
            await cls._trigger_surge(owner)
            current = cls._balance_points.get(owner_id, 0)

    @classmethod
    async def _trigger_surge(cls, owner: "Stats") -> None:
        owner_id = id(owner)
        attack_base = getattr(owner, "get_base_stat", None)
        base_atk = 0
        if callable(attack_base):
            try:
                base_atk = int(attack_base("atk"))
            except Exception:
                base_atk = int(getattr(owner, "_base_atk", getattr(owner, "atk", 0)))
        else:
            base_atk = int(getattr(owner, "_base_atk", getattr(owner, "atk", 0)))
        atk_bonus = max(1, int(base_atk * 0.22))
        surge_effect = StatEffect(
            name=f"{cls.id}_balance_surge_{owner_id}",
            stat_modifiers={
                "atk": atk_bonus,
                "crit_rate": 0.1,
                "spd": 1,
            },
            duration=2,
            source=cls.id,
        )
        owner.add_effect(surge_effect)

        allies = cls._resolve_allies(owner_id)
        luna = cls._resolve_luna(owner_id)
        await cls._pulse_support(owner, allies, luna)

    @classmethod
    def _apply_owner_aura(cls, owner: "Stats") -> None:
        owner_id = id(owner)
        attack_base = getattr(owner, "get_base_stat", None)
        base_atk = 0
        if callable(attack_base):
            try:
                base_atk = int(attack_base("atk"))
            except Exception:
                base_atk = int(getattr(owner, "_base_atk", getattr(owner, "atk", 0)))
        else:
            base_atk = int(getattr(owner, "_base_atk", getattr(owner, "atk", 0)))
        aura_effect = StatEffect(
            name=f"{cls.id}_oracle_aura_{owner_id}",
            stat_modifiers={
                "atk": max(1, int(base_atk * 0.18)),
                "mitigation": 0.15,
                "effect_resistance": 0.12,
                "crit_rate": 0.05,
            },
            duration=-1,
            source=cls.id,
        )
        owner.add_effect(aura_effect)

    @classmethod
    def _apply_link_aura(cls, owner: "Stats", luna: "Stats") -> None:
        owner_id = id(owner)
        aura_effect = StatEffect(
            name=f"{cls.id}_luna_link_{owner_id}",
            stat_modifiers={
                "atk": max(1, int(getattr(luna, "atk", 0) * 0.1)),
                "mitigation": 0.08,
                "effect_resistance": 0.08,
            },
            duration=-1,
            source=cls.id,
        )
        luna.add_effect(aura_effect)

    @classmethod
    async def _pulse_support(
        cls,
        owner: "Stats",
        allies: list["Stats"],
        luna: "Stats" | None,
    ) -> None:
        owner_id = id(owner)
        for ally in allies:
            if ally is owner or ally is None:
                continue
            support_effect = StatEffect(
                name=f"{cls.id}_ally_pulse_{owner_id}",
                stat_modifiers={
                    "mitigation": 0.08,
                    "effect_resistance": 0.05,
                },
                duration=2,
                source=cls.id,
            )
            ally.add_effect(support_effect)
            if ally is luna:
                await cls._apply_luna_guard(owner, luna)
            else:
                try:
                    ally.add_ultimate_charge(2)
                except Exception:
                    pass
                heal_amount = max(1, int(getattr(ally, "max_hp", 0) * 0.03))
                if heal_amount > 0:
                    try:
                        await ally.apply_healing(
                            heal_amount,
                            healer=owner,
                            source_type="passive",
                            source_name=cls.id,
                        )
                    except Exception:
                        pass
        if luna is not None and luna not in allies:
            await cls._apply_luna_guard(owner, luna)

    @classmethod
    async def _apply_luna_guard(cls, owner: "Stats", luna: "Stats") -> None:
        owner_id = id(owner)
        guard_effect = StatEffect(
            name=f"{cls.id}_luna_guard_{owner_id}",
            stat_modifiers={
                "mitigation": 0.12,
                "effect_resistance": 0.1,
            },
            duration=2,
            source=cls.id,
        )
        luna.add_effect(guard_effect)
        heal_amount = max(1, int(getattr(luna, "max_hp", 0) * 0.04))
        try:
            await luna.apply_healing(
                heal_amount,
                healer=owner,
                source_type="passive",
                source_name=cls.id,
            )
        except Exception:
            pass

    @classmethod
    async def _maybe_cache_party(
        cls,
        owner: "Stats",
        party: Sequence[object] | None,
    ) -> None:
        if party is None:
            return
        members = cls._normalize_party(party)
        if not members:
            return
        owner_id = id(owner)
        cls._ally_refs[owner_id] = [ref(member) for member in members]
        luna = cls._find_luna(members)
        if luna is not None:
            cls._luna_links[owner_id] = ref(luna)
            cls._ensure_luna_tracked(owner_id, luna)
            cls._apply_link_aura(owner, luna)

    @classmethod
    def _normalize_party(cls, party: Sequence[object]) -> list["Stats"]:
        normalized: list["Stats"] = []
        for member in party:
            stats = cls._extract_stats(member)
            if stats is not None:
                normalized.append(stats)
        return normalized

    @staticmethod
    def _extract_stats(member: object) -> "Stats" | None:
        if member is None:
            return None
        if hasattr(member, "hp") and hasattr(member, "add_effect"):
            return member  # type: ignore[return-value]
        stats = getattr(member, "stats", None)
        if stats is not None and hasattr(stats, "add_effect"):
            return stats
        return None

    @classmethod
    def _find_luna(cls, members: Iterable["Stats"]) -> "Stats" | None:
        for member in members:
            if getattr(member, "id", None) == "luna":
                return member
        return None

    @classmethod
    def _ensure_luna_tracked(cls, owner_id: int, luna: "Stats") -> None:
        refs = cls._ally_refs.setdefault(owner_id, [])
        for existing in refs:
            if existing() is luna:
                return
        refs.append(ref(luna))

    @classmethod
    def _resolve_luna(cls, owner_id: int) -> "Stats" | None:
        luna_ref = cls._luna_links.get(owner_id)
        if luna_ref is None:
            return None
        luna = luna_ref()
        if luna is None:
            cls._luna_links.pop(owner_id, None)
        return luna

    @classmethod
    def _resolve_allies(cls, owner_id: int) -> list["Stats"]:
        refs = cls._ally_refs.get(owner_id, [])
        resolved: list["Stats"] = []
        active_refs: list[ReferenceType["Stats"]] = []
        for stored in refs:
            member = stored()
            if member is None:
                continue
            resolved.append(member)
            active_refs.append(stored)
        if active_refs:
            cls._ally_refs[owner_id] = active_refs
        else:
            cls._ally_refs.pop(owner_id, None)
        return resolved

    @classmethod
    def _register_bus_handlers(cls, owner: "Stats") -> None:
        owner_id = id(owner)
        if owner_id in cls._bus_handlers:
            return
        owner_ref = ref(owner)

        async def _on_luna_hit(
            luna_owner: "Stats" | None,
            _sword: "Stats" | None,
            *_: object,
        ) -> None:
            tracked_owner = owner_ref()
            if tracked_owner is None:
                cls._teardown(owner_id, None)
                return
            if luna_owner is None:
                return
            cls._luna_links[owner_id] = ref(luna_owner)
            cls._ensure_luna_tracked(owner_id, luna_owner)
            cls._apply_link_aura(tracked_owner, luna_owner)
            await cls._add_balance(tracked_owner, cls.LUNA_HIT_GAIN)
            await cls._apply_luna_guard(tracked_owner, luna_owner)

        def _on_battle_end(entity: "Stats" | None) -> None:
            tracked_owner = owner_ref()
            if tracked_owner is None:
                cls._teardown(owner_id, None)
                return
            if entity is tracked_owner:
                cls._teardown(owner_id, tracked_owner)

        BUS.subscribe("luna_sword_hit", _on_luna_hit)
        BUS.subscribe("battle_end", _on_battle_end)
        cls._bus_handlers[owner_id] = {
            "luna_sword_hit": _on_luna_hit,
            "battle_end": _on_battle_end,
        }

    @classmethod
    def _teardown(cls, owner_id: int, owner: "Stats" | None) -> None:
        handlers = cls._bus_handlers.pop(owner_id, {})
        for event, callback in handlers.items():
            try:
                BUS.unsubscribe(event, callback)  # type: ignore[arg-type]
            except Exception:
                pass
        cls._balance_points.pop(owner_id, None)
        cls._balance_totals.pop(owner_id, None)
        cls._balance_carry.pop(owner_id, None)
        refs = cls._ally_refs.pop(owner_id, [])
        luna = cls._luna_links.pop(owner_id, None)
        if owner is not None:
            try:
                owner.remove_effect_by_source(cls.id)
            except Exception:
                pass
        for stored in refs:
            ally = stored()
            if ally is None:
                continue
            try:
                ally.remove_effect_by_source(cls.id)
            except Exception:
                pass
        if luna is not None:
            target = luna()
            if target is not None:
                try:
                    target.remove_effect_by_source(cls.id)
                except Exception:
                    pass

    async def on_defeat(self, owner: "Stats") -> None:
        self.__class__._teardown(id(owner), owner)

    @classmethod
    def get_balance(cls, owner: "Stats") -> int:
        return cls._balance_points.get(id(owner), 0)

    @classmethod
    def get_total_balance(cls, owner: "Stats") -> int:
        return cls._balance_totals.get(id(owner), 0)

    @classmethod
    def get_stacks(cls, owner: "Stats") -> int:
        return cls.get_total_balance(owner)

    @classmethod
    def get_display(cls, owner: "Stats") -> str:
        return "number" if cls.get_total_balance(owner) > cls.SOFT_CAP else cls.stack_display

    @classmethod
    def get_description(cls) -> str:
        return (
            "Starts battle with a permanent balance aura granting +18% of Ryne's base ATK, +15% mitigation, "
            "+12% Effect RES, and +5% crit rate. Links to Luna to share +10% of her base ATK along with +8% "
            "mitigation and Effect RES whenever she's present. Gains 2 balance from actions, 1 from hits, 4 "
            "from ultimates, and 2 whenever Luna's sword strikes; at 6 balance triggers a surge that grants "
            "Ryne +22% of her base ATK, +10% crit rate, and +1 SPD for 2 turns. Each surge pulses 8% "
            "mitigation, 5% Effect RES, +2 ultimate charge, and a 3% Max HP heal to other allies while "
            "refreshing Luna with 12% mitigation, 10% Effect RES, and a 4% Max HP heal. Balance stacks "
            "beyond 120 accrue at half speed but continue climbing without a hard cap; stack display switches "
            "to a numeric counter once past the soft cap."
        )
