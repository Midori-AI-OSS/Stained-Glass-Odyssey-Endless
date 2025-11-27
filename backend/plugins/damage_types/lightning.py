import asyncio
from dataclasses import dataclass

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
        """Zap all foes, seed random DoTs, and build Aftertaste stacks.

        Deprecated wrapper routed through the Lightning ultimate action.
        """

        from plugins.actions.ultimate.lightning_ultimate import LightningUltimate
        from plugins.actions.ultimate.utils import run_ultimate_action

        result = await run_ultimate_action(LightningUltimate, actor, allies, enemies)
        return bool(getattr(result, "success", False))

    @classmethod
    def get_ultimate_description(cls) -> str:
        return (
            "Deals the user's attack as damage to every enemy, then applies ten random "
            "DoT effects from all elements to each target. Each use grants an Aftertaste "
            "stack that later echoes extra hits based on the accumulated stacks. Damage "
            "and DoT rolls respect TURN_PACING adjustments."
        )
