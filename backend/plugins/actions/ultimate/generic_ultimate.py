"""Action plugin for the Generic damage type ultimate."""

from __future__ import annotations

from dataclasses import dataclass

from autofighter.passives import PassiveRegistry
from autofighter.stats import BUS
from plugins.actions.result import ActionResult
from plugins.actions.ultimate import UltimateActionBase


@dataclass(kw_only=True, slots=True)
class GenericUltimate(UltimateActionBase):
    """Split attack power into 64 rapid strikes on a single foe."""

    id: str = "ultimate.generic"
    name: str = "Neutral Frenzy"
    description: str = "Divide attack into 64 hits, triggering passive hooks for each one."
    damage_type_id: str = "Generic"

    async def execute(self, actor, targets, context):
        from autofighter.rooms.battle.pacing import pace_per_target
        from autofighter.rooms.battle.targeting import select_aggro_target

        result = ActionResult(success=True)
        enemies = list(context.enemies_of(actor))
        allies = list(context.allies_of(actor))
        foes = list(context.enemies_of(actor))
        registry = context.passive_registry or PassiveRegistry()

        await registry.trigger(
            "ultimate_used",
            actor,
            party=allies,
            foes=foes,
        )

        base = int(getattr(actor, "atk", 0))
        if base <= 0:
            result.messages.append("Generic ultimate skipped due to 0 attack")
            return result

        chunk = base // 64
        remainder = base % 64
        total_hits = 0

        for i in range(64):
            try:
                _, target = select_aggro_target(enemies)
            except ValueError:
                break
            if getattr(target, "hp", 0) <= 0:
                continue
            damage_value = chunk + (1 if i < remainder else 0)
            dealt = await target.apply_damage(
                damage_value,
                attacker=actor,
                action_name=self.name,
            )
            await pace_per_target(actor)
            target_id = str(getattr(target, "id", id(target)))
            result.damage_dealt[target_id] = result.damage_dealt.get(target_id, 0) + dealt
            total_hits += 1

            await BUS.emit_async("hit_landed", actor, target, dealt, "attack", "generic_ultimate")
            await registry.trigger_hit_landed(
                actor,
                target,
                dealt,
                "generic_ultimate",
                party=allies,
                foes=foes,
            )
            await registry.trigger(
                "action_taken",
                actor,
                target=target,
                damage=dealt,
                party=allies,
                foes=foes,
            )

        result.metadata = {"hits": total_hits, "damage": base}
        return result
