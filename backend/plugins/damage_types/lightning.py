import asyncio
from dataclasses import dataclass
import math
import random

from autofighter.effects import DamageOverTime
from autofighter.stats import BUS
from plugins import damage_effects
from plugins.damage_types._base import DamageTypeBase


@dataclass
class Lightning(DamageTypeBase):
    """Volatile element that detonates DoTs and spreads random shocks."""
    id: str = "Lightning"
    weakness: str = "Wind"
    color: tuple[int, int, int] = (255, 255, 0)

    def create_dot(self, damage: float, source) -> DamageOverTime | None:
        return damage_effects.create_dot(self.id, damage, source)

    def on_hit(self, attacker, target) -> None:
        mgr = getattr(target, "effect_manager", None)
        if mgr is None:
            return
        for effect in list(mgr.dots):
            dmg = int(effect.damage * 0.25)
            if dmg > 0:
                # Secondary chain lightning pings should not retrigger on-hit hooks
                # to avoid exponential task storms when dots are present.
                asyncio.create_task(
                    target.apply_damage(dmg, attacker=attacker, trigger_on_hit=False)
                )

    async def ultimate(self, actor, allies, enemies) -> bool:
        """Zap all foes, seed random DoTs, and build Aftertaste stacks."""
        from autofighter.rooms.battle.pacing import TURN_PACING
        from autofighter.rooms.battle.pacing import YIELD_MULTIPLIER
        from autofighter.rooms.battle.pacing import pace_per_target
        from autofighter.rooms.battle.pacing import pace_sleep
        from autofighter.rooms.battle.targeting import select_aggro_target
        from autofighter.rooms.battle.turn_loop import TURN_TIMEOUT_SECONDS

        if not await self.consume_ultimate(actor):
            return False

        # Lightning ultimate deals damage to all enemies and applies DoTs
        base_damage = int(getattr(actor, "atk", 0))

        hit_budget = sum(1 for enemy in enemies if getattr(enemy, "hp", 0) > 0)

        try:
            turn_pacing = float(TURN_PACING)
        except Exception:
            turn_pacing = 0.0

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
        for _ in range(hit_budget):
            try:
                _, enemy = select_aggro_target(enemies)
            except ValueError:
                break

            if base_damage > 0:
                await enemy.apply_damage(base_damage, attacker=actor, action_name="Lightning Ultimate")
                await wait_per_target()

            mgr = getattr(enemy, "effect_manager", None)
            if mgr is not None:
                types = ["Fire", "Ice", "Wind", "Lightning", "Light", "Dark"]
                dmg = int(getattr(actor, "atk", 0) * 0.05)
                dots_added = 0
                for _ in range(10):
                    effect = damage_effects.create_dot(random.choice(types), dmg, actor)
                    if effect is None:
                        continue
                    await mgr.add_dot(effect)
                    dots_added += 1

                if dots_added > 0:
                    await pace_sleep(YIELD_MULTIPLIER)

        # Set up aftertaste stacks
        stacks = getattr(actor, "_lightning_aftertaste_stacks", 0) + 1
        actor._lightning_aftertaste_stacks = stacks

        if not hasattr(actor, "_lightning_aftertaste_handler"):
            async def _hit(atk, tgt, amount, *_args) -> None:
                if atk is not actor:
                    return

                hits = getattr(actor, "_lightning_aftertaste_stacks", 0)
                if hits <= 0:
                    return

                from plugins.effects.aftertaste import Aftertaste

                await Aftertaste(hits=hits).apply(atk, tgt)

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
        return True

    @classmethod
    def get_ultimate_description(cls) -> str:
        return (
            "Deals the user's attack as damage to every enemy, then applies ten random "
            "DoT effects from all elements to each target. Each use grants an Aftertaste "
            "stack that later echoes extra hits based on the accumulated stacks. Damage "
            "and DoT rolls respect TURN_PACING adjustments."
        )
