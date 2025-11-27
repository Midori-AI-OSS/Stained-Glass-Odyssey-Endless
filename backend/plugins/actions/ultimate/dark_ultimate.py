"""Action plugin for Dark damage type ultimate."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from autofighter.stats import BUS
from plugins.actions.result import ActionResult
from plugins.actions.ultimate import UltimateActionBase


@dataclass(kw_only=True, slots=True)
class DarkUltimate(UltimateActionBase):
    """Strike a foe multiple times based on allied DoT stacks."""

    id: str = "ultimate.dark"
    name: str = "Eclipse Devastation"
    description: str = "Unleash six crushing blows scaled by allied DoT stacks."
    damage_type_id: str = "Dark"
    ULT_PER_STACK: ClassVar[float] = 1.005

    async def execute(self, actor, targets, context):
        from autofighter.rooms.battle.pacing import pace_per_target
        from autofighter.rooms.battle.targeting import select_aggro_target

        result = ActionResult(success=True)
        allies = list(context.allies_of(actor))
        enemies = list(context.enemies_of(actor))
        living = [enemy for enemy in enemies if getattr(enemy, "hp", 0) > 0]
        if not living:
            result.success = False
            result.messages.append("No valid targets for Dark ultimate")
            return result

        stacks = 0
        for member in allies:
            manager = getattr(member, "effect_manager", None)
            if manager is not None:
                stacks += len(getattr(manager, "dots", []))
            else:
                stacks += len(getattr(member, "dots", []))

        base_atk = float(getattr(actor, "atk", 0))
        multiplier = self.ULT_PER_STACK ** stacks
        damage_value = int(base_atk * multiplier)
        damage_value = max(damage_value, 0)

        for _ in range(6):
            try:
                _, target = select_aggro_target(enemies)
            except ValueError:
                break
            dealt = await target.apply_damage(
                damage_value,
                attacker=actor,
                action_name=self.name,
            )
            await pace_per_target(actor)
            target_id = str(getattr(target, "id", id(target)))
            result.damage_dealt[target_id] = result.damage_dealt.get(target_id, 0) + dealt
            await BUS.emit_async("damage", actor, target, dealt)

        result.metadata = {"stacks": stacks, "damage": damage_value}
        return result
