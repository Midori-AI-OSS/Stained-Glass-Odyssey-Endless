"""Action plugin for Ice damage type ultimate."""

from __future__ import annotations

from dataclasses import dataclass

from plugins.actions.result import ActionResult
from plugins.actions.ultimate import UltimateActionBase


@dataclass(kw_only=True, slots=True)
class IceUltimate(UltimateActionBase):
    """Strike all foes with ramping waves of cold damage."""

    id: str = "ultimate.ice"
    name: str = "Permafrost Rhapsody"
    description: str = "Deliver six waves of attacks that grow 30% stronger per target."
    damage_type_id: str = "Ice"

    async def execute(self, actor, targets, context):
        from autofighter.rooms.battle.pacing import pace_per_target
        from autofighter.rooms.battle.targeting import select_aggro_target

        result = ActionResult(success=True)
        enemies = list(context.enemies_of(actor))
        base = int(getattr(actor, "atk", 0))
        if base <= 0:
            result.messages.append("Ice ultimate lacks sufficient attack power")
            return result

        total_hits = 0
        for _ in range(6):
            living = [foe for foe in enemies if getattr(foe, "hp", 0) > 0]
            if not living:
                break
            bonus = 1.0
            wave_hits = 0
            for _ in range(len(living)):
                try:
                    _, target = select_aggro_target(enemies)
                except ValueError:
                    living = []
                    break
                damage_value = int(base * bonus)
                dealt = await target.apply_damage(
                    damage_value,
                    attacker=actor,
                    action_name=self.name,
                )
                await pace_per_target(actor)
                target_id = str(getattr(target, "id", id(target)))
                result.damage_dealt[target_id] = result.damage_dealt.get(target_id, 0) + dealt
                bonus += 0.3
                wave_hits += 1
                total_hits += 1
            if wave_hits > 0:
                await pace_per_target(actor)

        result.metadata = {"damage": base, "hits": total_hits}
        return result
