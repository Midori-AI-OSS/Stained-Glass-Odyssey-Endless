"""Graygray's counter-focused special ability action."""

from __future__ import annotations

from dataclasses import dataclass

from autofighter.stat_effect import StatEffect
from plugins.actions import ActionCostBreakdown, ActionResult, TargetingRules, TargetScope, TargetSide
from plugins.actions.special import SpecialAbilityBase


@dataclass(kw_only=True, slots=True)
class GraygrayCounterOpus(SpecialAbilityBase):
    """Adopt a defensive stance that amplifies counters."""

    plugin_type = "action"
    id: str = "special.graygray.counter_opus"
    name: str = "Counter Opus"
    description: str = (
        "Enter a disciplined stance that raises defense and mitigation, priming the next wave of counters."
    )
    character_id: str = "graygray"
    cooldown_turns: int = 2
    cost: ActionCostBreakdown = ActionCostBreakdown(action_points=1)
    targeting: TargetingRules = TargetingRules(
        scope=TargetScope.SELF,
        side=TargetSide.ALLY,
    )

    async def execute(self, actor, targets, context):
        """Apply a defensive buff to Graygray."""

        defense_bonus = max(30, int(getattr(actor, "defense", 0) * 0.3))
        mitigation_bonus = 0.2
        effect = StatEffect(
            name=f"{self.id}_stance",
            stat_modifiers={"defense": defense_bonus, "mitigation": mitigation_bonus},
            duration=2,
            source=self.id,
        )
        actor.add_effect(effect)

        actor_id = str(getattr(actor, "id", id(actor)))
        result = ActionResult(success=True)
        result.effects_applied.append((actor_id, effect.name))
        result.messages.append(
            f"{getattr(actor, 'id', 'Graygray')} assumes a counter stance, gaining {defense_bonus} DEF."
        )
        return result
