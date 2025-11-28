"""Action plugin for Fire damage type ultimate."""

from __future__ import annotations

from dataclasses import dataclass

from plugins.actions.result import ActionResult
from plugins.actions.ultimate import UltimateActionBase


@dataclass(kw_only=True, slots=True)
class FireUltimate(UltimateActionBase):
    """Blast all foes with the caster's attack and roll burning DoTs."""

    id: str = "ultimate.fire"
    name: str = "Inferno Bloom"
    description: str = "Deal attack damage to all living foes and attempt to ignite them."
    damage_type_id: str = "Fire"

    async def execute(self, actor, targets, context):
        from autofighter.rooms.battle.pacing import pace_per_target
        from autofighter.rooms.battle.targeting import select_aggro_target

        result = ActionResult(success=True)
        enemies = list(context.enemies_of(actor))
        living_count = sum(1 for foe in enemies if getattr(foe, "hp", 0) > 0)
        base = int(getattr(actor, "atk", 0))
        if base <= 0 or living_count <= 0:
            result.messages.append("No damage dealt by Fire ultimate")
            return result

        for _ in range(living_count):
            try:
                _, foe = select_aggro_target(enemies)
            except ValueError:
                break
            dealt = await foe.apply_damage(
                base,
                attacker=actor,
                action_name=self.name,
            )
            await pace_per_target(actor)
            target_id = str(getattr(foe, "id", id(foe)))
            result.damage_dealt[target_id] = result.damage_dealt.get(target_id, 0) + dealt

            manager = getattr(foe, "effect_manager", None)
            if manager is None:
                manager = context.effect_manager_for(foe)
                foe.effect_manager = manager
            try:
                await manager.maybe_inflict_dot(actor, dealt)
            except Exception:
                pass

        result.metadata = {"hits": living_count, "damage": base}
        return result
