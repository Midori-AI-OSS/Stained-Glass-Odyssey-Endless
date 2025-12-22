"""Ixia's lightning-themed special ability action."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field

from autofighter.stat_effect import StatEffect
from plugins.actions import ActionCostBreakdown
from plugins.actions import ActionResult
from plugins.actions import TargetingRules
from plugins.actions import TargetScope
from plugins.actions import TargetSide
from plugins.actions.special import SpecialAbilityBase


@dataclass(kw_only=True, slots=True)
class IxiaLightningBurst(SpecialAbilityBase):
    """Release a burst of lightning that shocks a foe."""

    plugin_type = "action"
    id: str = "special.ixia.lightning_burst"
    name: str = "Lightning Burst"
    description: str = "Condense storm power into a single foe, then leave them vulnerable."
    character_id: str = "ixia"
    cooldown_turns: int = 2
    cost: ActionCostBreakdown = field(
        default_factory=lambda: ActionCostBreakdown(action_points=1)
    )
    targeting: TargetingRules = field(
        default_factory=lambda: TargetingRules(
            scope=TargetScope.SINGLE,
            side=TargetSide.ENEMY,
            max_targets=1,
        )
    )

    async def execute(self, actor, targets, context):
        """Strike one foe and reduce their defenses temporarily."""

        enemies = context.enemies_of(actor)
        target = targets[0] if targets else None
        if target is None and enemies:
            target = enemies[0]
        if target is None:
            return ActionResult(success=False, messages=[f"{self.name} has no target."])

        damage = max(1.0, float(getattr(actor, "atk", 0)) * 1.3)
        hit = await context.apply_damage(
            actor,
            target,
            damage,
            metadata={"action_name": self.name},
        )

        defense_cut = -max(15, int(getattr(target, "defense", 0) * 0.2))
        vulnerability = StatEffect(
            name=f"{self.id}_vulnerability",
            stat_modifiers={"defense": defense_cut},
            duration=2,
            source=self.id,
        )
        target.add_effect(vulnerability)

        target_id = str(getattr(target, "id", id(target)))
        result = ActionResult(success=True)
        result.damage_dealt[target_id] = hit
        result.effects_applied.append((target_id, vulnerability.name))
        result.messages.append(
            f"{getattr(actor, 'id', 'Ixia')} shocks {getattr(target, 'id', 'foe')} for {hit} damage."
        )
        return result
