"""Carly's guardian-themed special ability action."""

from __future__ import annotations

from dataclasses import dataclass

from autofighter.stat_effect import StatEffect
from plugins.actions import ActionCostBreakdown
from plugins.actions import ActionResult
from plugins.actions import TargetScope
from plugins.actions import TargetSide
from plugins.actions import TargetingRules
from plugins.actions.special import SpecialAbilityBase


def _lowest_health_ally(allies):
    """Return the living ally with the lowest health percentage."""

    living = [ally for ally in allies if getattr(ally, "hp", 0) > 0]
    if not living:
        return None
    return min(
        living,
        key=lambda ally: (getattr(ally, "hp", 0) / max(getattr(ally, "max_hp", 1), 1)),
    )


@dataclass(kw_only=True, slots=True)
class CarlyGuardianBarrier(SpecialAbilityBase):
    """Heals and shields the most injured ally."""

    plugin_type = "action"
    id: str = "special.carly.guardian_barrier"
    name: str = "Guardian Barrier"
    description: str = "Project a luminous bulwark that heals and grants mitigation to an ally."
    character_id: str = "carly"
    cooldown_turns: int = 3
    cost: ActionCostBreakdown = ActionCostBreakdown(action_points=1)
    targeting: TargetingRules = TargetingRules(
        scope=TargetScope.SINGLE,
        side=TargetSide.ALLY,
        max_targets=1,
        allow_self=True,
    )

    async def execute(self, actor, targets, context):
        """Heal the lowest health ally and add a mitigation buff."""

        allies = context.allies_of(actor)
        chosen = targets[0] if targets else None
        if chosen is None:
            chosen = _lowest_health_ally(allies)
        if chosen is None:
            return ActionResult(success=False, messages=[f"{self.name} found no allies to protect."])

        defense = max(1, int(getattr(actor, "defense", 0)))
        healing_amount = max(60, int(defense * 0.8))
        healed = await context.apply_healing(
            actor,
            chosen,
            healing_amount,
            overheal_allowed=True,
            source_type="special",
            source_name=self.name,
        )

        mitigation_bonus = StatEffect(
            name=f"{self.id}_mitigation",
            stat_modifiers={"mitigation": 0.15},
            duration=2,
            source=self.id,
        )
        chosen.add_effect(mitigation_bonus)

        target_id = str(getattr(chosen, "id", id(chosen)))
        result = ActionResult(success=True)
        result.healing_done[target_id] = healed
        result.effects_applied.append((target_id, mitigation_bonus.name))
        result.messages.append(
            f"{getattr(actor, 'id', 'Carly')} shields {getattr(chosen, 'id', 'ally')} with a guardian barrier!"
        )
        return result
