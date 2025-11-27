"""Action plugin for Wind damage type ultimate."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field

from autofighter.effects import EffectManager
from autofighter.effects import create_stat_buff
from autofighter.stats import BUS
from plugins.actions import TargetScope
from plugins.actions import TargetSide
from plugins.actions import TargetingRules
from plugins.actions.result import ActionResult
from plugins.actions.ultimate import UltimateActionBase


@dataclass(kw_only=True, slots=True)
class WindUltimate(UltimateActionBase):
    """Fan out rapid strikes across all living enemies."""

    id: str = "ultimate.wind"
    name: str = "Gale Tempest"
    description: str = "Split attack power into rapid hits with heightened effect hit rate."
    damage_type_id: str = "Wind"
    targeting: TargetingRules = field(
        default_factory=lambda: TargetingRules(
            scope=TargetScope.ALL,
            side=TargetSide.ENEMY,
            include_summons=True,
        )
    )

    async def execute(self, actor, targets, context):
        from autofighter.rooms.battle.pacing import pace_per_target
        from autofighter.rooms.battle.targeting import select_aggro_target

        result = ActionResult(success=True)
        enemies = list(context.enemies_of(actor))
        living = [foe for foe in enemies if getattr(foe, "hp", 0) > 0]

        actor_manager = getattr(actor, "effect_manager", None)
        if actor_manager is None:
            actor_manager = context.effect_manager_for(actor)
            actor.effect_manager = actor_manager

        modifier = create_stat_buff(
            actor,
            name="wind_ultimate_effect_hit",
            turns=1,
            effect_hit_rate_mult=1.5,
        )
        await actor_manager.add_modifier(modifier)

        hits = int(getattr(actor, "wind_ultimate_hits", getattr(actor, "ultimate_hits", 25)) or 25)
        hits = max(1, hits)
        base_attack = max(1, int(getattr(actor, "atk", 0)))

        if not living:
            try:
                modifier.remove()
            except Exception:
                pass
            result.messages.append("No living foes for Wind ultimate")
            return result

        total_chunks = hits * len(living)
        per = base_attack // total_chunks if total_chunks > 0 else base_attack
        remainder = base_attack - (per * total_chunks)
        per = max(per, 0)

        effect_managers: dict[object, EffectManager] = {}

        for _ in range(total_chunks):
            try:
                _, target = select_aggro_target(enemies)
            except ValueError:
                break
            if getattr(target, "hp", 0) <= 0:
                continue
            extra = 1 if remainder > 0 else 0
            if remainder > 0:
                remainder -= 1
            damage_value = max(1, int(per + extra))
            dealt = await target.apply_damage(
                damage_value,
                attacker=actor,
                action_name=self.name,
            )
            await pace_per_target(actor)
            target_id = str(getattr(target, "id", id(target)))
            result.damage_dealt[target_id] = result.damage_dealt.get(target_id, 0) + dealt
            await BUS.emit_async("hit_landed", actor, target, dealt, "attack", "wind_ultimate")

            manager = effect_managers.get(target)
            if manager is None:
                manager = getattr(target, "effect_manager", None)
                if manager is None:
                    manager = context.effect_manager_for(target)
                    target.effect_manager = manager
                effect_managers[target] = manager
            try:
                await manager.maybe_inflict_dot(actor, dealt)
            except Exception:
                pass

        try:
            modifier.remove()
        except Exception:
            pass

        result.metadata = {
            "damage_type": self.damage_type_id,
            "hits": total_chunks,
        }
        return result
