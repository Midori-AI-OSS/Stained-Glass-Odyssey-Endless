import asyncio
from dataclasses import dataclass
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
        if not getattr(actor, "use_ultimate", lambda: False)():
            return False

        # Lightning ultimate deals damage to all enemies and applies DoTs
        base_damage = int(getattr(actor, "atk", 0))

        # Apply damage to all enemies
        for enemy in enemies:
            if base_damage > 0:
                await enemy.apply_damage(base_damage, attacker=actor, action_name="Lightning Ultimate")
                await asyncio.sleep(0.002)

            # Apply random DoTs to each enemy
            mgr = getattr(enemy, "effect_manager", None)
            if mgr is not None:
                types = ["Fire", "Ice", "Wind", "Lightning", "Light", "Dark"]
                dmg = int(getattr(actor, "atk", 0) * 0.05)
                for _ in range(10):
                    effect = damage_effects.create_dot(random.choice(types), dmg, actor)
                    if effect is not None:
                        mgr.add_dot(effect)
                    await asyncio.sleep(0.002)

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
            "stack that later echoes extra hits based on the accumulated stacks."
        )
