"""Action plugin for Lightning damage type ultimate."""

from __future__ import annotations

from dataclasses import dataclass
import math
import random

from autofighter.stats import BUS
from plugins import damage_effects
from plugins.actions.result import ActionResult
from plugins.actions.ultimate import UltimateActionBase


@dataclass(kw_only=True, slots=True)
class LightningUltimate(UltimateActionBase):
    """Zap all foes, then seed random DoTs and build Aftertaste stacks."""

    id: str = "ultimate.lightning"
    name: str = "Storm Chorus"
    description: str = "Strike every enemy, apply random DoTs, and gain Aftertaste stacks."
    damage_type_id: str = "Lightning"

    async def execute(self, actor, targets, context):
        from autofighter.rooms.battle.pacing import TURN_PACING
        from autofighter.rooms.battle.pacing import YIELD_MULTIPLIER
        from autofighter.rooms.battle.pacing import pace_per_target
        from autofighter.rooms.battle.pacing import pace_sleep
        from autofighter.rooms.battle.targeting import select_aggro_target
        from autofighter.rooms.battle.turn_loop import TURN_TIMEOUT_SECONDS

        result = ActionResult(success=True)
        enemies = list(context.enemies_of(actor))
        base_damage = int(getattr(actor, "atk", 0))
        hit_budget = sum(1 for enemy in enemies if getattr(enemy, "hp", 0) > 0)

        try:
            turn_pacing = float(TURN_PACING)
        except Exception:
            turn_pacing = 0.5

        if not math.isfinite(turn_pacing) or turn_pacing <= 0:
            turn_pacing = 0.5

        try:
            timeout_seconds = float(TURN_TIMEOUT_SECONDS)
        except Exception:
            timeout_seconds = 35.0

        if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
            timeout_seconds = 35.0

        max_pacing_seconds = max(timeout_seconds - turn_pacing, 0.0)
        pacing_seconds = 0.0
        pacing_budget_spent = False

        async def wait_per_target(duration: float | None = None) -> None:
            nonlocal pacing_seconds
            nonlocal pacing_budget_spent

            if pacing_budget_spent:
                await pace_sleep(YIELD_MULTIPLIER)
                return

            multiplier = await pace_per_target(actor, duration=duration)
            wait_seconds = max(multiplier, 0.0) * turn_pacing
            pacing_seconds += wait_seconds
            if pacing_seconds >= max_pacing_seconds:
                pacing_budget_spent = True

        if base_damage <= 0 or hit_budget <= 0:
            result.messages.append("Lightning ultimate has no effect")
            return result

        total_damage = 0
        for _ in range(hit_budget):
            try:
                _, enemy = select_aggro_target(enemies)
            except ValueError:
                break
            if getattr(enemy, "hp", 0) <= 0:
                continue

            dealt = await enemy.apply_damage(
                base_damage,
                attacker=actor,
                action_name=self.name,
            )
            await wait_per_target()
            target_id = str(getattr(enemy, "id", id(enemy)))
            result.damage_dealt[target_id] = result.damage_dealt.get(target_id, 0) + dealt
            total_damage += dealt

            manager = getattr(enemy, "effect_manager", None)
            if manager is not None:
                dot_types = ["Fire", "Ice", "Wind", "Lightning", "Light", "Dark"]
                dot_damage = int(getattr(actor, "atk", 0) * 0.05)
                dots_added = 0
                for _ in range(10):
                    effect = damage_effects.create_dot(random.choice(dot_types), dot_damage, actor)
                    if effect is None:
                        continue
                    await manager.add_dot(effect)
                    dots_added += 1
                if dots_added > 0:
                    await pace_sleep(YIELD_MULTIPLIER)

        stacks = getattr(actor, "_lightning_aftertaste_stacks", 0) + 1
        actor._lightning_aftertaste_stacks = stacks

        if not hasattr(actor, "_lightning_aftertaste_handler"):
            async def _hit(attacker, target, amount, *_args) -> None:
                if attacker is not actor:
                    return
                hits = getattr(actor, "_lightning_aftertaste_stacks", 0)
                if hits <= 0:
                    return
                from plugins.effects.aftertaste import Aftertaste

                await Aftertaste(hits=hits).apply(attacker, target)

            def _clear(_):
                BUS.unsubscribe("hit_landed", _hit)
                BUS.unsubscribe("battle_end", _clear)
                if hasattr(actor, "_lightning_aftertaste_stacks"):
                    delattr(actor, "_lightning_aftertaste_stacks")
                if hasattr(actor, "_lightning_aftertaste_handler"):
                    delattr(actor, "_lightning_aftertaste_handler")

            BUS.subscribe("hit_landed", _hit)
            BUS.subscribe("battle_end", _clear)
            actor._lightning_aftertaste_handler = _hit

        result.metadata = {
            "damage": total_damage,
            "stacks": stacks,
            "hits": hit_budget,
        }
        return result
