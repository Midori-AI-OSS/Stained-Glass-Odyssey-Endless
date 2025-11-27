"""Compatibility helpers for legacy ultimate hooks."""

from __future__ import annotations

from typing import Sequence

from autofighter.passives import PassiveRegistry
from autofighter.stats import BUS
from plugins.actions import BattleContext
from plugins.actions.registry import ActionRegistry
from plugins.actions.ultimate import UltimateActionBase


async def run_ultimate_action(
    action_cls: type[UltimateActionBase],
    actor,
    allies: Sequence,
    enemies: Sequence,
):
    """Execute an ultimate action outside of the turn loop."""

    action = action_cls()
    effect_managers: dict[str, object] = {}
    for combatant in list(allies) + list(enemies):
        manager = getattr(combatant, "effect_manager", None)
        if manager is None:
            continue
        key = str(getattr(combatant, "id", id(combatant)))
        effect_managers[key] = manager

    context = BattleContext(
        turn=0,
        run_id="legacy",
        phase="legacy",
        actor=actor,
        allies=list(allies),
        enemies=list(enemies),
        action_registry=ActionRegistry(),
        passive_registry=PassiveRegistry(),
        effect_managers=effect_managers,
        summon_manager=None,
        event_bus=BUS,
        enrage_state=None,
        visual_queue=None,
        damage_router=None,
    )

    targets = action.get_valid_targets(actor, context.allies, context.enemies)
    return await action.run(actor, targets, context)
