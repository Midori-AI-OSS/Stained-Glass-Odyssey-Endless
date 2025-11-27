from dataclasses import dataclass

from autofighter.effects import DamageOverTime
from autofighter.stats import BUS
from plugins import damage_effects
from plugins.damage_types._base import DamageTypeBase


@dataclass
class Light(DamageTypeBase):
    """Supportive element that heals allies and purges harmful effects."""
    id: str = "Light"
    weakness: str = "Dark"
    color: tuple[int, int, int] = (255, 255, 255)

    def create_dot(self, damage: float, source) -> DamageOverTime | None:
        return damage_effects.create_dot(self.id, damage, source)

    async def on_action(self, actor, allies, enemies):
        from autofighter.rooms.battle.pacing import pace_per_target

        for ally in allies:
            if getattr(ally, "hp", 0) <= 0:
                continue
            mgr = getattr(ally, "effect_manager", None)
            if mgr is not None:
                hot = damage_effects.create_hot(self.id, actor)
                if hot is not None:
                    await mgr.add_hot(hot)
            await pace_per_target(actor)

        for ally in allies:
            max_hp = getattr(ally, "max_hp", 0)
            if max_hp <= 0:
                continue
            hp = getattr(ally, "hp", 0)
            if hp <= 0:
                continue
            if hp / max_hp < 0.25:
                await ally.apply_healing(actor.atk, healer=actor)
                await pace_per_target(actor)
                return False
            await pace_per_target(actor)

        return True

    async def ultimate(self, actor, allies, enemies):
        """Fully heal allies, cleanse their DoTs, and weaken enemies.

        Deprecated: routed through the Light ultimate action plugin.
        """

        from plugins.actions.ultimate.light_ultimate import LightUltimate
        from plugins.actions.ultimate.utils import run_ultimate_action

        result = await run_ultimate_action(LightUltimate, actor, allies, enemies)
        await BUS.emit_async("light_ultimate", actor)
        return bool(getattr(result, "success", False))

    @classmethod
    def get_ultimate_description(cls) -> str:
        return (
            "Removes all DoTs from allies, then heals them to full. Enemies receive a 25% defense "
            "debuff for 10 turns and a 'light_ultimate' event is emitted. Healing and debuff "
            "application steps respect TURN_PACING via the pacing helper."
        )
