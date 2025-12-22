"""Shared base classes and helper policies for action plugins."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum
import math
from typing import TYPE_CHECKING, ClassVar, Sequence

if TYPE_CHECKING:  # pragma: no cover - type checking only
    from autofighter.stats import Stats

    from .context import BattleContext
    from .result import ActionResult


class ActionType(StrEnum):
    """Supported action categories."""

    NORMAL = "normal"
    SPECIAL = "special"
    PASSIVE = "passive"
    ULTIMATE = "ultimate"
    ITEM = "item"


class TargetSide(StrEnum):
    """Describes which team a targeting rule can select from."""

    ENEMY = "enemy"
    ALLY = "ally"
    ANY = "any"


class TargetScope(StrEnum):
    """Describes how many entities an action may select."""

    SINGLE = "single"
    MULTI = "multi"
    ALL = "all"
    SELF = "self"


@dataclass(slots=True)
class ActionAnimationPlan:
    """Metadata consumed by the pacing helpers."""

    name: str = ""
    duration: float = 0.0
    per_target: float = 0.0

    @classmethod
    def empty(cls) -> "ActionAnimationPlan":
        return cls()


@dataclass(slots=True)
class ActionCostBreakdown:
    """Simple resource policy for action plugins."""

    action_points: int = 1
    health_percent: float = 0.0
    resources: dict[str, int] = field(default_factory=dict)

    def can_pay(self, actor: "Stats", context: "BattleContext") -> bool:
        """Validate that the actor has enough resources for this action."""

        if self.action_points and getattr(actor, "action_points", 0) < self.action_points:
            return False
        if self.health_percent > 0:
            max_hp = getattr(actor, "max_hp", 0) or getattr(actor, "hp", 0)
            health_cost = math.ceil(max_hp * self.health_percent)
            if getattr(actor, "hp", 0) <= health_cost:
                return False
        for resource, amount in self.resources.items():
            if resource == "ultimate_charge":
                current = getattr(actor, "ultimate_charge", 0)
            else:
                current = getattr(actor, resource, 0)
            if current < amount:
                return False
        return True

    def apply(self, actor: "Stats", context: "BattleContext") -> None:
        """Deduct the configured costs after the action resolves."""

        if self.action_points:
            actor.action_points = max(actor.action_points - self.action_points, 0)
        if self.health_percent > 0:
            max_hp = getattr(actor, "max_hp", 0) or getattr(actor, "hp", 0)
            health_cost = math.ceil(max_hp * self.health_percent)
            actor.hp = max(actor.hp - health_cost, 1)
        for resource, amount in self.resources.items():
            context.spend_resource(actor, resource, amount)


@dataclass(slots=True)
class TargetingRules:
    """Common targeting helpers shared by all actions."""

    scope: TargetScope = TargetScope.SINGLE
    side: TargetSide = TargetSide.ENEMY
    max_targets: int = 1
    allow_self: bool = False
    include_downed: bool = False
    include_summons: bool = False

    def validate(
        self,
        actor: "Stats",
        targets: Sequence["Stats"],
        context: "BattleContext",
    ) -> bool:
        """Return True when the provided targets satisfy this policy."""

        if self.scope is TargetScope.SELF:
            return all(target is actor for target in targets)
        if not targets:
            return False
        allowed = {
            id(target)
            for target in self.filter_targets(
                actor,
                context.allies_of(actor),
                context.enemies_of(actor),
                limit=False,
            )
        }
        if not allowed:
            return False
        if self.scope is TargetScope.ALL:
            return all(id(target) in allowed for target in targets)
        if len(targets) > self.max_targets:
            return False
        return all(id(target) in allowed for target in targets)

    def filter_targets(
        self,
        actor: "Stats",
        allies: Sequence["Stats"],
        enemies: Sequence["Stats"],
        *,
        limit: bool = True,
    ) -> list["Stats"]:
        """Return the default candidate list for this policy."""

        if self.scope is TargetScope.SELF:
            return [actor]
        pool: list["Stats"]
        if self.side is TargetSide.ALLY:
            pool = list(allies)
        elif self.side is TargetSide.ENEMY:
            pool = list(enemies)
        else:
            pool = list(allies) + list(enemies)
        if not self.include_downed:
            pool = [target for target in pool if getattr(target, "hp", 0) > 0]
        if not self.include_summons:
            pool = [target for target in pool if not getattr(target, "is_summon", False)]
        if not self.allow_self:
            pool = [target for target in pool if target is not actor]
        if self.scope is TargetScope.ALL:
            return pool
        if not limit:
            return pool
        if self.scope is TargetScope.SINGLE and pool:
            return [pool[0]]
        return pool[: self.max_targets]


@dataclass(kw_only=True, slots=True)
class ActionBase(ABC):
    """Base class for all combat action plugins."""

    plugin_type: ClassVar[str] = "action"

    id: str
    name: str
    description: str
    action_type: ActionType = ActionType.NORMAL
    tags: tuple[str, ...] = ()
    targeting: TargetingRules = field(default_factory=TargetingRules)
    cost: ActionCostBreakdown = field(default_factory=ActionCostBreakdown)
    cooldown_turns: int = 0
    animation: ActionAnimationPlan = field(default_factory=ActionAnimationPlan.empty)

    async def can_execute(
        self,
        actor: "Stats",
        targets: Sequence["Stats"],
        context: "BattleContext",
    ) -> bool:
        """Return True when the action can be performed immediately."""

        registry = getattr(context, "action_registry", None)
        if registry is not None and not registry.is_available(actor, self):
            return False
        if not self.cost.can_pay(actor, context):
            return False
        if not self.targeting.validate(actor, targets, context):
            return False
        return await self._can_execute(actor, targets, context)

    async def run(
        self,
        actor: "Stats",
        targets: Sequence["Stats"],
        context: "BattleContext",
    ) -> "ActionResult":
        """Execute the action with policy enforcement."""

        if not await self.can_execute(actor, targets, context):
            raise RuntimeError(f"Action {self.id} cannot execute in the current context")
        result = await self.execute(actor, targets, context)
        self.cost.apply(actor, context)
        if self.cooldown_turns and getattr(context, "action_registry", None) is not None:
            context.action_registry.start_cooldown(actor, self)
        return result

    @abstractmethod
    async def execute(
        self,
        actor: "Stats",
        targets: Sequence["Stats"],
        context: "BattleContext",
    ) -> "ActionResult":
        """Perform the action effect and return a structured result."""

    def get_valid_targets(
        self,
        actor: "Stats",
        allies: Sequence["Stats"],
        enemies: Sequence["Stats"],
    ) -> list["Stats"]:
        """Convenience helper for callers to compute default targets."""

        return self.targeting.filter_targets(actor, allies, enemies)

    async def _can_execute(
        self,
        actor: "Stats",
        targets: Sequence["Stats"],
        context: "BattleContext",
    ) -> bool:
        """Subclass hook for additional gating (e.g., combo requirements)."""

        return True
