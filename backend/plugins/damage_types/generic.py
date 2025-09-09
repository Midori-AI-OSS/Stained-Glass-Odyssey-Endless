import asyncio
from dataclasses import dataclass

from autofighter.passives import PassiveRegistry
from plugins.damage_types._base import DamageTypeBase


@dataclass
class Generic(DamageTypeBase):
    """Neutral element with no strengths or weaknesses.

    Serves as the baseline damage type focused on consistent damage without
    side effects.
    """

    id: str = "Generic"
    weakness: str = "none"
    color: tuple[int, int, int] = (255, 255, 255)

    async def ultimate(self, actor, allies, enemies):
        """Split the user's attack into 64 rapid strikes on one target."""
        if not getattr(actor, "use_ultimate", lambda: False)():
            return False

        from autofighter.stats import BUS  # Import here to avoid circular imports

        registry = PassiveRegistry()
        target_pool = (
            [a for a in allies if a.hp > 0]
            if getattr(actor, "plugin_type", "") == "foe"
            else [e for e in enemies if e.hp > 0]
        )
        if not target_pool:
            return True
        target = target_pool[0]

        base = actor.atk // 64
        remainder = actor.atk % 64
        for i in range(64):
            dmg = base + (1 if i < remainder else 0)
            await target.apply_damage(
                dmg, attacker=actor, action_name="Generic Ultimate"
            )
            await BUS.emit_async(
                "hit_landed", actor, target, dmg, "attack", "generic_ultimate"
            )
            await registry.trigger_hit_landed(
                actor,
                target,
                dmg,
                "generic_ultimate",
                party=allies,
                foes=enemies,
            )
            await registry.trigger(
                "action_taken",
                actor,
                target=target,
                damage=dmg,
                party=allies,
                foes=enemies,
            )
            if i % 5 == 0:
                await asyncio.sleep(0)
        return True
