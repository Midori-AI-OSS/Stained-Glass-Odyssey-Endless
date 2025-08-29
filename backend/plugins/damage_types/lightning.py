import asyncio
from dataclasses import dataclass
import random

from autofighter.effects import DamageOverTime
from autofighter.stats import BUS
from plugins import damage_effects
from plugins.damage_types._base import DamageTypeBase


@dataclass
class Lightning(DamageTypeBase):
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

    def ultimate(self, attacker, target) -> None:
        if not getattr(attacker, "use_ultimate", lambda: False)():
            return
        mgr = getattr(target, "effect_manager", None)
        if mgr is not None:
            types = ["Fire", "Ice", "Wind", "Lightning", "Light", "Dark"]
            dmg = int(getattr(attacker, "atk", 0) * 0.05)
            for _ in range(10):
                effect = damage_effects.create_dot(random.choice(types), dmg, attacker)
                if effect is not None:
                    mgr.add_dot(effect)

        stacks = getattr(attacker, "_lightning_aftertaste_stacks", 0) + 1
        attacker._lightning_aftertaste_stacks = stacks

        if not hasattr(attacker, "_lightning_aftertaste_handler"):
            def _hit(atk, tgt, amount, *_args) -> None:
                if atk is attacker:
                    from plugins.effects.aftertaste import Aftertaste

                    asyncio.create_task(
                        Aftertaste(
                            hits=getattr(attacker, "_lightning_aftertaste_stacks", 0)
                        ).apply(atk, tgt)
                    )

            def _clear(_):
                BUS.unsubscribe("hit_landed", _hit)
                BUS.unsubscribe("battle_end", _clear)
                if hasattr(attacker, "_lightning_aftertaste_stacks"):
                    delattr(attacker, "_lightning_aftertaste_stacks")
                if hasattr(attacker, "_lightning_aftertaste_handler"):
                    delattr(attacker, "_lightning_aftertaste_handler")

            BUS.subscribe("hit_landed", _hit)
            BUS.subscribe("battle_end", _clear)
            attacker._lightning_aftertaste_handler = _hit
