"""Ally's tactical special ability action."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from typing import Sequence

from plugins.actions import ActionCostBreakdown
from plugins.actions import ActionResult
from plugins.actions import TargetingRules
from plugins.actions import TargetScope
from plugins.actions import TargetSide
from plugins.actions.special import SpecialAbilityBase


def _normalize_targets(
    provided: Sequence[object],
    fallback: Sequence[object],
    max_targets: int,
) -> list[object]:
    """Return at most ``max_targets`` targets, reusing fallbacks as needed."""

    targets = [target for target in provided if getattr(target, "hp", 0) > 0]
    if not targets:
        for candidate in fallback:
            if getattr(candidate, "hp", 0) <= 0:
                continue
            targets.append(candidate)
            if len(targets) >= max_targets:
                break
    return targets[:max_targets]


@dataclass(kw_only=True, slots=True)
class AllyOverloadCascade(SpecialAbilityBase):
    """Chain elemental strikes across multiple foes."""

    plugin_type = "action"
    id: str = "special.ally.overload_cascade"
    name: str = "Overload Cascade"
    description: str = (
        "Arc lightning-infused daggers between two foes, dealing moderate damage "
        "to each target."
    )
    character_id: str = "ally"
    cooldown_turns: int = 3
    cost: ActionCostBreakdown = field(
        default_factory=lambda: ActionCostBreakdown(action_points=1)
    )
    targeting: TargetingRules = field(
        default_factory=lambda: TargetingRules(
            scope=TargetScope.MULTI,
            side=TargetSide.ENEMY,
            max_targets=2,
        )
    )

    async def execute(self, actor, targets, context):
        """Strike up to two enemies with cascading damage."""

        enemies = context.enemies_of(actor)
        actual_targets = _normalize_targets(targets, enemies, self.targeting.max_targets)
        if not actual_targets:
            return ActionResult(success=False, messages=[f"{self.name} fizzles with no foes."])

        base_damage = max(1.0, float(getattr(actor, "atk", 0)) * 0.7)
        result = ActionResult(success=True)
        for target in actual_targets:
            metadata = {"action_name": self.name}
            damage = await context.apply_damage(actor, target, base_damage, metadata=metadata)
            target_id = str(getattr(target, "id", id(target)))
            result.damage_dealt[target_id] = damage
            result.messages.append(
                f"{getattr(actor, 'id', 'Ally')} overloads {getattr(target, 'id', 'foe')} for {damage} damage."
            )
        return result
