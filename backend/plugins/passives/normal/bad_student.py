from __future__ import annotations

from dataclasses import dataclass
import random
from typing import TYPE_CHECKING
from typing import ClassVar
from weakref import ReferenceType
from weakref import ref

from autofighter.stat_effect import StatEffect
from autofighter.stats import BUS

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class _BadStudentStack:
    turns: int
    delta: float


class BadStudentBase:
    """Shared logic for Jennifer Feltmann's disciplinary debuffs."""

    trigger = "hit_landed"
    stack_display = "pips"
    stack_duration: ClassVar[int] = 3
    stack_strength: ClassVar[float] = 0.75
    attack_chance_ratio: ClassVar[float] = 0.05
    ultimate_chance_ratio: ClassVar[float] = 1.5
    min_actions_per_turn: ClassVar[float] = 0.1
    min_application_chance: ClassVar[float] = 0.01

    _tracked_targets: ClassVar[dict[int, list[_BadStudentStack]]]
    _target_refs: ClassVar[dict[int, ReferenceType["Stats"]]]
    _stack_counters: ClassVar[dict[int, int]]
    _turn_handler = None
    _battle_end_handler = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._tracked_targets = {}
        cls._target_refs = {}
        cls._stack_counters = {}
        cls._turn_handler = None
        cls._battle_end_handler = None

    async def apply(self, owner: "Stats", event: str = "hit_landed", **kwargs: object) -> None:
        """Handle hit_landed events to apply detention stacks."""

        resolved_event = (kwargs.get("event") or event or "").lower()
        if resolved_event != "hit_landed":
            return

        target = kwargs.get("hit_target")
        if target is None:
            return

        is_ultimate = self._is_ultimate_action(kwargs.get("action_type")) or bool(
            kwargs.get("is_ultimate")
        )
        chance = self._resolve_application_chance(owner, target, is_ultimate)
        if chance <= 0:
            return
        if random.random() >= chance:
            return

        applied = self._apply_stack(target)
        if applied <= 0:
            return

        self._record_marker(target)

    def _apply_stack(self, target: "Stats") -> float:
        """Apply a stack to the target and track its decay."""

        cls = type(self)
        current = self._extract_actions(target)
        desired = max(self.min_actions_per_turn, current - cls.stack_strength)
        delta = max(0.0, current - desired)
        if delta <= 0:
            return 0.0

        target.actions_per_turn = desired

        entity_id = id(target)
        cls._tracked_targets.setdefault(entity_id, []).append(
            _BadStudentStack(turns=cls.stack_duration, delta=delta)
        )
        cls._target_refs[entity_id] = ref(target)
        cls._register_event_hooks()
        return delta

    @classmethod
    def _extract_actions(cls, target: "Stats") -> float:
        try:
            return float(getattr(target, "actions_per_turn", 1.0))
        except (TypeError, ValueError):
            return 1.0

    def _record_marker(self, target: "Stats") -> None:
        cls = type(self)
        entity_id = id(target)
        counter = cls._stack_counters.get(entity_id, 0) + 1
        cls._stack_counters[entity_id] = counter
        marker = StatEffect(
            name=f"{self.id}_marker_{entity_id}_{counter}",
            stat_modifiers={},
            duration=cls.stack_duration,
            source=self.id,
        )
        target.add_effect(marker)

    def _resolve_application_chance(
        self,
        owner: "Stats",
        target: "Stats",
        is_ultimate: bool,
    ) -> float:
        try:
            effect_hit = float(max(0.0, owner.effect_hit_rate))
        except (AttributeError, TypeError, ValueError):
            effect_hit = 0.0

        try:
            resistance = float(max(0.0, target.effect_resistance))
        except (AttributeError, TypeError, ValueError):
            resistance = 0.0

        multiplier = (
            self.ultimate_chance_ratio if is_ultimate else self.attack_chance_ratio
        )
        raw = effect_hit * multiplier
        effective = raw - resistance
        # Always allow at least a 1% discipline chance.
        clamped = max(self.min_application_chance, min(1.0, effective))
        return clamped

    @staticmethod
    def _is_ultimate_action(action_type: object | None) -> bool:
        if isinstance(action_type, str):
            lowered = action_type.lower()
            return "ultimate" in lowered
        return False

    @classmethod
    def _register_event_hooks(cls) -> None:
        if cls._turn_handler is not None:
            return

        async def _on_turn_start(entity: "Stats | None", *_: object) -> None:
            if entity is None:
                return
            await cls._process_turn_start(entity)

        async def _on_battle_end(*_: object, **__: object) -> None:
            await cls._reset_state()

        cls._turn_handler = _on_turn_start
        cls._battle_end_handler = _on_battle_end
        BUS.subscribe("turn_start", _on_turn_start)
        BUS.subscribe("battle_end", _on_battle_end)

    @classmethod
    async def _process_turn_start(cls, entity: "Stats") -> None:
        entity_id = id(entity)
        stacks = cls._tracked_targets.get(entity_id)
        if not stacks:
            return

        remaining: list[_BadStudentStack] = []
        restored = 0.0
        for stack in stacks:
            stack.turns -= 1
            if stack.turns > 0:
                remaining.append(stack)
            else:
                restored += stack.delta

        if restored > 0:
            entity.actions_per_turn = max(
                cls.min_actions_per_turn, entity.actions_per_turn + restored
            )

        if remaining:
            cls._tracked_targets[entity_id] = remaining
            return

        cls._tracked_targets.pop(entity_id, None)
        cls._target_refs.pop(entity_id, None)
        cls._stack_counters.pop(entity_id, None)
        cls._maybe_cleanup_handlers()

    @classmethod
    async def _reset_state(cls) -> None:
        for entity_id, stacks in list(cls._tracked_targets.items()):
            total = sum(stack.delta for stack in stacks)
            if total <= 0:
                continue
            entity_ref = cls._target_refs.get(entity_id)
            entity = entity_ref() if entity_ref is not None else None
            if entity is None:
                continue
            entity.actions_per_turn = max(
                cls.min_actions_per_turn, entity.actions_per_turn + total
            )

        cls._tracked_targets.clear()
        cls._target_refs.clear()
        cls._stack_counters.clear()
        cls._maybe_cleanup_handlers(force=True)

    @classmethod
    def _maybe_cleanup_handlers(cls, force: bool = False) -> None:
        if not force and cls._tracked_targets:
            return

        if cls._turn_handler is not None:
            BUS.unsubscribe("turn_start", cls._turn_handler)
            cls._turn_handler = None

        if cls._battle_end_handler is not None:
            BUS.unsubscribe("battle_end", cls._battle_end_handler)
            cls._battle_end_handler = None


@dataclass
class BadStudent(BadStudentBase):
    """Normal-tier implementation of the Bad Student passive."""

    plugin_type = "passive"
    id = "bad_student"
    name = "Bad Student"


__all__ = ["BadStudent", "BadStudentBase"]
