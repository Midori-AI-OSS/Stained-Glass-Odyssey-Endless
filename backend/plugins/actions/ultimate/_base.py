"""Base classes for ultimate action plugins."""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from dataclasses import field
from typing import TYPE_CHECKING
from typing import Sequence

from plugins.actions._base import ActionBase
from plugins.actions._base import ActionCostBreakdown
from plugins.actions._base import ActionType
from plugins.actions._base import TargetScope
from plugins.actions._base import TargetSide
from plugins.actions._base import TargetingRules

if TYPE_CHECKING:  # pragma: no cover - type checking only
    from autofighter.stats import Stats

    from plugins.actions.context import BattleContext
    from plugins.actions.result import ActionResult


@dataclass(kw_only=True, slots=True)
class UltimateActionBase(ActionBase):
    """Common helpers for all ultimate action plugins."""

    action_type: ActionType = ActionType.ULTIMATE
    targeting: TargetingRules = field(
        default_factory=lambda: TargetingRules(
            scope=TargetScope.ALL,
            side=TargetSide.ENEMY,
            include_summons=True,
        )
    )
    cost: ActionCostBreakdown = field(
        default_factory=lambda: ActionCostBreakdown(action_points=0)
    )
    ultimate_cost: int = 15
    damage_type_id: str = "Generic"

    async def can_execute(
        self,
        actor: "Stats",
        targets: Sequence["Stats"],
        context: "BattleContext",
    ) -> bool:
        """Check ultimate readiness and basic action policies."""

        if not getattr(actor, "ultimate_ready", False):
            return False
        registry = getattr(context, "action_registry", None)
        if registry is not None and not registry.is_available(actor, self):
            return False
        if not self.cost.can_pay(actor, context):
            return False
        if targets and not self.targeting.validate(actor, targets, context):
            return False
        return await self._can_execute(actor, targets, context)

    async def run(
        self,
        actor: "Stats",
        targets: Sequence["Stats"],
        context: "BattleContext",
    ) -> "ActionResult":
        """Execute the ultimate and consume the underlying charge."""

        from plugins.actions.result import ActionResult  # Local import to avoid cycle

        if not await self.can_execute(actor, targets, context):
            raise RuntimeError(f"Ultimate {self.id} cannot execute in the current context")

        await self._consume_charge(actor)
        result = await self.execute(actor, targets, context)
        if not isinstance(result, ActionResult):
            raise TypeError("Ultimate actions must return an ActionResult")
        self.cost.apply(actor, context)
        if self.cooldown_turns and getattr(context, "action_registry", None) is not None:
            context.action_registry.start_cooldown(actor, self)
        return result

    async def _consume_charge(self, actor: "Stats") -> None:
        """Consume the actor's ultimate gauge while emitting events."""

        use_ultimate = getattr(actor, "use_ultimate", None)
        consumed = False
        if callable(use_ultimate):
            outcome = use_ultimate()
            if inspect.isawaitable(outcome):
                consumed = await outcome
            else:
                consumed = bool(outcome)
        if not consumed:
            actor.ultimate_charge = 0
            actor.ultimate_ready = False


__all__ = ["UltimateActionBase"]
