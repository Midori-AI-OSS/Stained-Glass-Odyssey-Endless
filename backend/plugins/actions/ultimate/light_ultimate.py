"""Action plugin for Light damage type ultimates."""

from __future__ import annotations

import contextlib
from dataclasses import dataclass
from dataclasses import field

from autofighter.effects import create_stat_buff
from autofighter.stats import BUS
from plugins.actions import TargetingRules
from plugins.actions import TargetScope
from plugins.actions import TargetSide
from plugins.actions.result import ActionResult
from plugins.actions.ultimate import UltimateActionBase


@dataclass(kw_only=True, slots=True)
class LightUltimate(UltimateActionBase):
    """Cleanse and heal allies while weakening foes."""

    id: str = "ultimate.light"
    name: str = "Radiant Salvation"
    description: str = "Cleanse allies, heal them to full, and debuff enemies."
    damage_type_id: str = "Light"
    targeting: TargetingRules = field(
        default_factory=lambda: TargetingRules(
            scope=TargetScope.ALL,
            side=TargetSide.ANY,
            allow_self=True,
        )
    )

    async def execute(self, actor, targets, context):
        from autofighter.rooms.battle.pacing import pace_per_target

        result = ActionResult(success=True)
        allies = list(context.allies_of(actor))
        enemies = list(context.enemies_of(actor))

        for ally in allies:
            if getattr(ally, "hp", 0) <= 0:
                continue
            manager = getattr(ally, "effect_manager", None)
            if manager is None:
                manager = context.effect_manager_for(ally)
                ally.effect_manager = manager
            removed_dots = []
            for dot in list(getattr(manager, "dots", [])):
                try:
                    manager.dots.remove(dot)
                except ValueError:
                    continue
                dots_attr = getattr(ally, "dots", None)
                if isinstance(dots_attr, list):
                    with contextlib.suppress(ValueError):
                        dots_attr.remove(dot.id)
                removed_dots.append(dot)
            for dot in removed_dots:
                BUS.emit_batched(
                    "dot_cleansed",
                    actor,
                    ally,
                    getattr(dot, "id", None),
                    {
                        "dot_name": getattr(dot, "name", None),
                        "remaining_turns": getattr(dot, "turns", None),
                        "dot_damage": getattr(dot, "damage", None),
                    },
                )
                result.effects_removed.append(
                    (
                        str(getattr(ally, "id", id(ally))),
                        getattr(dot, "id", "dot"),
                    )
                )

            missing = max(getattr(ally, "max_hp", 0) - getattr(ally, "hp", 0), 0)
            if missing > 0:
                healed = await context.apply_healing(
                    actor,
                    ally,
                    missing,
                    source_type="ultimate",
                    source_name=self.name,
                )
                result.healing_done[str(getattr(ally, "id", id(ally)))] = healed
            await pace_per_target(actor)

        for enemy in enemies:
            if getattr(enemy, "hp", 0) <= 0:
                continue
            manager = getattr(enemy, "effect_manager", None)
            if manager is None:
                manager = context.effect_manager_for(enemy)
                enemy.effect_manager = manager
            modifier = create_stat_buff(
                enemy,
                name="light_ultimate_def_down",
                turns=10,
                defense_mult=0.75,
            )
            await manager.add_modifier(modifier)
            result.effects_applied.append(
                (str(getattr(enemy, "id", id(enemy))), modifier.id)
            )
            await pace_per_target(actor)

        await BUS.emit_async("light_ultimate", actor)
        result.metadata = {
            "damage_type": self.damage_type_id,
            "allies_affected": len(allies),
            "enemies_debuffed": sum(1 for foe in enemies if getattr(foe, "hp", 0) > 0),
        }
        return result
