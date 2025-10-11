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
class _PhoenixRestInterval(HealingOverTime):
    """Helper HoT effect that intercepts the next action for Phoenix Respite."""

    owner_id: int = 0

    async def tick(self, target: "Stats", *_: object) -> bool:
        """Keep the helper active until the intercept completes."""

        if getattr(target, "hp", 0) <= 0:
            return False
        return True

    async def on_action(self, target: "Stats") -> bool:
        return await CasnoPhoenixRespite._complete_rest(target, self)


@dataclass
class CasnoPhoenixRespite:
    """Casno's Phoenix Respite passive enabling restorative downtime."""

    plugin_type = "passive"
    id = "casno_phoenix_respite"
    name = "Phoenix Respite"
    trigger = "action_taken"
    stack_display = "number"

    _action_counts: ClassVar[dict[int, int]] = {}
    _rest_stacks: ClassVar[dict[int, int]] = {}
    _pending_rest: ClassVar[dict[int, bool]] = {}
    _helper_effect_ids: ClassVar[dict[int, str]] = {}
    _battle_end_handlers: ClassVar[dict[int, Callable[..., None]]] = {}

    async def apply(self, target: "Stats", **_: object) -> None:
        """Track actions and schedule Phoenix Respite downtime."""

        entity_id = id(target)
        cls = type(self)

        cls._register_battle_end(target)
        cls._rest_stacks.setdefault(entity_id, 0)
        cls._action_counts[entity_id] = cls._action_counts.get(entity_id, 0) + 1

        if cls._pending_rest.get(entity_id):
            return

        if cls._action_counts[entity_id] < 5:
            return

        cls._action_counts[entity_id] = 0
        await cls._schedule_rest(target)

    @classmethod
    async def _schedule_rest(cls, target: "Stats") -> None:
        if getattr(target, "hp", 0) <= 0:
            return

        entity_id = id(target)
        effect_manager = getattr(target, "effect_manager", None)
        if effect_manager is None:
            return

        helper_id = cls._helper_effect_name(entity_id)
        for hot in list(getattr(effect_manager, "hots", [])):
            if getattr(hot, "id", "") == helper_id:
                cls._pending_rest[entity_id] = True
                return

        helper_effect = _PhoenixRestInterval(
            name=f"{cls.id}_rest_interval",
            healing=0,
            turns=-1,
            id=helper_id,
            source=target,
            owner_id=entity_id,
        )

        cls._pending_rest[entity_id] = True
        cls._helper_effect_ids[entity_id] = helper_id
        await effect_manager.add_hot(helper_effect)
        cls._register_battle_end(target)

    @classmethod
    async def _complete_rest(
        cls,
        target: "Stats",
        helper: _PhoenixRestInterval,
    ) -> bool:
        entity_id = id(target)

        cls._pending_rest[entity_id] = False

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
        target.hp = target.max_hp

        stacks = cls._rest_stacks.get(entity_id, 0) + 1
        cls._rest_stacks[entity_id] = stacks

        cls._apply_rest_boost(target, stacks)

        return False

    @classmethod
    def _apply_rest_boost(cls, target: "Stats", stacks: int) -> None:
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
        for stat in stat_names:
            base_value = target.get_base_stat(stat)
            bonus = base_value * 0.55 * stacks
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
        cls._pending_rest.pop(entity_id, None)
        cls._action_counts.pop(entity_id, None)

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
        return cls._rest_stacks.get(id(target), 0)

    @classmethod
    def _helper_effect_name(cls, entity_id: int) -> str:
        return f"{cls.id}_rest_helper_{entity_id}"

    @classmethod
    def _boost_effect_name(cls, entity_id: int) -> str:
        return f"{cls.id}_rest_boost_{entity_id}"


def get_stacks(target: "Stats") -> int:
    return CasnoPhoenixRespite.get_stacks(target)


__all__ = ["CasnoPhoenixRespite", "get_stacks"]
