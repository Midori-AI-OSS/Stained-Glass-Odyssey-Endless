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

    # Override fields with class attributes for PluginLoader compatibility
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

        Replicates the existing hardcoded normal attack logic from the turn loop,
        including metadata preparation, damage application, event emissions,
        multi-hit/spread handling, DoT application, and passive triggers.
        """

        from autofighter.rooms.battle.turn_loop.player_turn import (
            prepare_action_attack_metadata,
        )

        result = ActionResult(success=True)

        # Validate we have at least one target
        if not targets:
            result.success = False
            result.messages.append("No valid targets")
            return result

        # Primary target is the first one
        target = targets[0]

        # Prepare attack metadata for tracking
        metadata_dict = prepare_action_attack_metadata(actor)
        metadata_dict["action_name"] = self.name

        # Apply damage to primary target
        damage = await context.apply_damage(
            actor,
            target,
            float(getattr(actor, "atk", 0)),
            metadata=metadata_dict,
        )

        # Track damage dealt using target ID
        target_id = str(getattr(target, "id", id(target)))
        result.damage_dealt[target_id] = damage

        # Emit events for the action
        damage_type = getattr(actor, "damage_type", None)
        damage_type_id = (
            getattr(damage_type, "id", "generic")
            if damage_type
            else "generic"
        )

        if damage <= 0:
            result.messages.append(
                f"{getattr(actor, 'id', 'Actor')}'s attack was dodged by {getattr(target, 'id', 'Target')}"
            )
        else:
            result.messages.append(
                f"{getattr(actor, 'id', 'Actor')} hits {getattr(target, 'id', 'Target')} for {damage}"
            )

            # Emit hit_landed event
            if context.event_bus:
                await context.event_bus.emit_async(
                    "hit_landed",
                    actor,
                    target,
                    damage,
                    "attack",
                    f"{damage_type_id}_attack",
                )

            # Trigger passive registry hit_landed
            if context.passive_registry:
                try:
                    await context.passive_registry.trigger_hit_landed(
                        actor,
                        target,
                        damage,
                        "attack",
                        damage_type=damage_type_id,
                        party=list(context.allies),
                        foes=list(context.enemies),
                    )
                except Exception:
                    pass  # Passive trigger failures should not break the action

        # Apply DoT if applicable
        target_effect_manager = context.effect_manager_for(target)
        try:
            await target_effect_manager.maybe_inflict_dot(actor, damage)
        except Exception:
            pass  # DoT application failures should not break the action

        # Handle multi-hit/spread mechanics from damage type
        targets_hit = 1
        if damage_type is not None:
            get_turn_spread = getattr(damage_type, "get_turn_spread", None)
            if callable(get_turn_spread):
                try:
                    spread_behavior = get_turn_spread()
                    if spread_behavior is not None:
                        # Note: Full spread implementation would require access to
                        # the target index and more turn loop helpers. For now,
                        # we document that spread is not fully supported in the
                        # plugin until the turn loop integration is complete.
                        pass
                except Exception:
                    pass

        # Emit action_used event
        if context.event_bus:
            await context.event_bus.emit_async("action_used", actor, target, damage)

        # Trigger passive registry action_taken
        if context.passive_registry:
            try:
                await context.passive_registry.trigger(
                    "action_taken",
                    actor,
                    target=target,
                    damage=damage,
                    party=list(context.allies),
                    foes=list(context.enemies),
                )
            except Exception:
                pass

        # Record metadata
        result.metadata = {
            "damage_type": damage_type_id,
            "targets_hit": targets_hit,
            **metadata_dict,
        }

        return result
