"""Placeholder normal attack action."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from typing import TYPE_CHECKING
from typing import Sequence

from plugins.actions import ActionAnimationPlan
from plugins.actions import ActionBase
from plugins.actions import ActionCostBreakdown
from plugins.actions import ActionType
from plugins.actions import TargetingRules
from plugins.actions import TargetScope
from plugins.actions import TargetSide
from plugins.actions.result import ActionResult

if TYPE_CHECKING:  # pragma: no cover - type checking only
    from autofighter.stats import Stats
    from plugins.actions.context import BattleContext


@dataclass(kw_only=True, slots=True)
class BasicAttackAction(ActionBase):
    """Stub for the existing hardcoded basic attack."""

    id: str = "normal.basic_attack"
    name: str = "Basic Attack"
    description: str = "Strike the foe with your equipped weapon."
    action_type: ActionType = ActionType.NORMAL
    tags: tuple[str, ...] = ("normal_attack",)
    targeting: TargetingRules = field(
        default_factory=lambda: TargetingRules(
            scope=TargetScope.SINGLE,
            side=TargetSide.ENEMY,
            max_targets=1,
        )
    )
    cost: ActionCostBreakdown = field(
        default_factory=lambda: ActionCostBreakdown(action_points=1)
    )
    animation: ActionAnimationPlan = field(
        default_factory=lambda: ActionAnimationPlan(
            name="basic_attack",
            duration=0.45,
            per_target=0.2,
        )
    )

    async def execute(
        self,
        actor: "Stats",
        targets: Sequence["Stats"],
        context: "BattleContext",
    ) -> ActionResult:
        """Run the normal attack damage sequence.

        The full damage, mitigation, and passive orchestration is implemented in
        task b60f5a58 when the existing turn-loop logic moves into this plugin.
        """

        raise NotImplementedError("Basic attack execution will land with task b60f5a58")
