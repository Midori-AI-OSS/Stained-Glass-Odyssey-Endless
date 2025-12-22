"""Becca's supportive special ability action."""

from __future__ import annotations

from dataclasses import dataclass

from autofighter.stat_effect import StatEffect
from plugins.actions import ActionCostBreakdown, ActionResult, TargetingRules, TargetScope, TargetSide
from plugins.actions.special import SpecialAbilityBase


@dataclass(kw_only=True, slots=True)
class BeccaMenagerieConvergence(SpecialAbilityBase):
    """Focus Becca's summons into a short-lived stat surge."""

    plugin_type = "action"
    id: str = "special.becca.menagerie_convergence"
    name: str = "Menagerie Convergence"
    description: str = (
        "Blend spectral familiars into Becca's stance, granting a burst of attack and "
        "defense before the constructs disperse."
    )
    character_id: str = "becca"
    cooldown_turns: int = 4
    cost: ActionCostBreakdown = ActionCostBreakdown(action_points=1)
    targeting: TargetingRules = TargetingRules(
        scope=TargetScope.SELF,
        side=TargetSide.ALLY,
    )

    async def execute(self, actor, targets, context):
        """Amplify Becca's stats for several turns and provide a light heal."""

        atk_bonus = max(30, int(getattr(actor, "atk", 0) * 0.25))
        def_bonus = max(20, int(getattr(actor, "defense", 0) * 0.2))
        modifier = StatEffect(
            name=f"{self.id}_buff",
            stat_modifiers={"atk": atk_bonus, "defense": def_bonus},
            duration=3,
            source=self.id,
        )
        actor.add_effect(modifier)

        healing = await context.apply_healing(
            actor,
            actor,
            max(50, int(getattr(actor, "atk", 0) * 0.35)),
            overheal_allowed=True,
            source_type="special",
            source_name=self.name,
        )

        actor_id = str(getattr(actor, "id", id(actor)))
        result = ActionResult(success=True)
        result.healing_done[actor_id] = healing
        result.effects_applied.append((actor_id, modifier.name))
        result.messages.append(
            f"{getattr(actor, 'id', 'Becca')} channels her menagerie, gaining {atk_bonus} ATK and {def_bonus} DEF."
        )
        return result
