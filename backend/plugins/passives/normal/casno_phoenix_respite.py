from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import Callable
from typing import ClassVar
from weakref import ref

from autofighter.effects import HealingOverTime
from autofighter.stat_effect import StatEffect
from autofighter.stats import BUS

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class _RelaxedMomentumPause(HealingOverTime):
    """Helper HoT that intercepts the next action for Relaxed momentum upkeep."""

    owner_id: int = 0

    async def tick(self, target: "Stats", *_: object) -> bool:
        """Keep the helper active until the intercept completes."""

        if getattr(target, "hp", 0) <= 0:
            return False
        return True

    async def on_action(self, target: "Stats") -> bool:
        return await CasnoPhoenixRespite._complete_relaxed_cycle(target, self)


@dataclass
class CasnoPhoenixRespite:
    """Casno's Phoenix Respite passive empowering Relaxed battle pacing."""

    plugin_type = "passive"
    id = "casno_phoenix_respite"
    name = "Phoenix Respite"
    trigger = "action_taken"
    stack_display = "number"

    _attack_counts: ClassVar[dict[int, int]] = {}
    _relaxed_stacks: ClassVar[dict[int, int]] = {}
    _relaxed_converted: ClassVar[dict[int, int]] = {}
    _pending_relaxed: ClassVar[dict[int, bool]] = {}
    _helper_effect_ids: ClassVar[dict[int, str]] = {}
    _battle_end_handlers: ClassVar[dict[int, Callable[..., None]]] = {}

    async def apply(self, target: "Stats", **_: object) -> None:
        """Track actions and schedule Phoenix Respite downtime."""

        entity_id = id(target)
        cls = type(self)

        cls._register_battle_end(target)
        cls._relaxed_stacks.setdefault(entity_id, 0)
        cls._relaxed_converted.setdefault(entity_id, 0)
        cls._attack_counts[entity_id] = cls._attack_counts.get(entity_id, 0) + 1

        if cls._pending_relaxed.get(entity_id):
            return

        if cls._attack_counts[entity_id] < 5:
            return

        cls._attack_counts[entity_id] = 0
        stacks = cls._relaxed_stacks.get(entity_id, 0) + 1
        cls._relaxed_stacks[entity_id] = stacks

        if stacks <= 50:
            return

        await cls._schedule_relaxed_pause(target)

    @classmethod
    async def _schedule_relaxed_pause(cls, target: "Stats") -> None:
        if getattr(target, "hp", 0) <= 0:
            return

        entity_id = id(target)
        effect_manager = getattr(target, "effect_manager", None)
        if effect_manager is None:
            return

        helper_id = cls._helper_effect_name(entity_id)
        for hot in list(getattr(effect_manager, "hots", [])):
            if getattr(hot, "id", "") == helper_id:
                cls._pending_relaxed[entity_id] = True
                return

        helper_effect = _RelaxedMomentumPause(
            name=f"{cls.id}_relaxed_interval",
            healing=0,
            turns=-1,
            id=helper_id,
            source=target,
            owner_id=entity_id,
        )

        cls._pending_relaxed[entity_id] = True
        cls._helper_effect_ids[entity_id] = helper_id
        await effect_manager.add_hot(helper_effect)
        cls._register_battle_end(target)

    @classmethod
    async def _complete_relaxed_cycle(
        cls,
        target: "Stats",
        helper: _RelaxedMomentumPause,
    ) -> bool:
        entity_id = id(target)

        cls._pending_relaxed[entity_id] = False

        effect_manager = getattr(target, "effect_manager", None)
        if effect_manager is not None:
            try:
                effect_manager.hots.remove(helper)
            except ValueError:
                pass
        try:
            while helper.id in target.hots:
                target.hots.remove(helper.id)
        except Exception:
            pass

        cls._helper_effect_ids.pop(entity_id, None)

        target.action_points = max(target.action_points - 1, 0)

        missing_hp = max(target.max_hp - target.hp, 0)
        if missing_hp > 0:
            try:
                await target.apply_healing(
                    missing_hp,
                    healer=target,
                    source_type="passive",
                    source_name=cls.id,
                )
            except Exception:
                pass

        available = cls._relaxed_stacks.get(entity_id, 0)
        consumed = min(5, available)
        if consumed:
            cls._relaxed_stacks[entity_id] = max(available - consumed, 0)

        total_converted = cls._relaxed_converted.get(entity_id, 0) + consumed
        cls._relaxed_converted[entity_id] = total_converted

        cls._apply_relaxed_boost(target, total_converted)
        target.hp = target.max_hp

        return False

    @classmethod
    def _apply_relaxed_boost(cls, target: "Stats", converted_stacks: int) -> None:
        effect_name = cls._boost_effect_name(id(target))
        target.remove_effect_by_name(effect_name)

        stat_names = [
            "max_hp",
            "atk",
            "defense",
            "crit_rate",
            "crit_damage",
            "effect_hit_rate",
            "effect_resistance",
            "mitigation",
            "vitality",
            "regain",
            "dodge_odds",
            "spd",
        ]

        modifiers: dict[str, float | int] = {}
        multiplier = 0.15 * converted_stacks
        for stat in stat_names:
            base_value = target.get_base_stat(stat)
            bonus = base_value * multiplier
            if isinstance(base_value, int):
                bonus = int(bonus)
            modifiers[stat] = bonus

        effect = StatEffect(
            name=effect_name,
            stat_modifiers=modifiers,
            duration=-1,
            source=cls.id,
        )
        target.add_effect(effect)

    @classmethod
    def get_display(cls, target: "Stats") -> str:  # noqa: ARG003 - required signature
        """Expose Relaxed momentum as a numeric stack counter for the UI."""
        return "number"

    @classmethod
    def _register_battle_end(cls, target: "Stats") -> None:
        entity_id = id(target)
        if entity_id in cls._battle_end_handlers:
            return

        target_ref = ref(target)

        def _on_battle_end(*_args: object, **_kwargs: object) -> None:
            BUS.unsubscribe("battle_end", _on_battle_end)
            cls._battle_end_handlers.pop(entity_id, None)
            tracked = target_ref()
            if tracked is not None:
                cls._clear_pending_state(tracked)

        BUS.subscribe("battle_end", _on_battle_end)
        cls._battle_end_handlers[entity_id] = _on_battle_end

    @classmethod
    def _clear_pending_state(cls, target: "Stats") -> None:
        entity_id = id(target)

        handler = cls._battle_end_handlers.pop(entity_id, None)
        if handler is not None:
            BUS.unsubscribe("battle_end", handler)

        helper_id = cls._helper_effect_ids.pop(entity_id, None)
        cls._pending_relaxed.pop(entity_id, None)
        cls._attack_counts.pop(entity_id, None)
        cls._relaxed_stacks.pop(entity_id, None)
        cls._relaxed_converted.pop(entity_id, None)

        effect_manager = getattr(target, "effect_manager", None)
        if effect_manager is not None and helper_id is not None:
            for hot in list(effect_manager.hots):
                if getattr(hot, "id", "") == helper_id:
                    effect_manager.hots.remove(hot)
        try:
            while helper_id and helper_id in target.hots:
                target.hots.remove(helper_id)
        except Exception:
            pass

    async def on_defeat(self, target: "Stats") -> None:
        self._clear_pending_state(target)

    @classmethod
    def get_stacks(cls, target: "Stats") -> int:
        return cls._relaxed_stacks.get(id(target), 0)

    @classmethod
    def _helper_effect_name(cls, entity_id: int) -> str:
        return f"{cls.id}_relaxed_helper_{entity_id}"

    @classmethod
    def _boost_effect_name(cls, entity_id: int) -> str:
        return f"{cls.id}_relaxed_boost_{entity_id}"


def get_stacks(target: "Stats") -> int:
    return CasnoPhoenixRespite.get_stacks(target)


__all__ = ["CasnoPhoenixRespite", "get_stacks"]
