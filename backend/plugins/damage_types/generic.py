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
        from autofighter.rooms.battle.pacing import pace_per_target
        from autofighter.rooms.battle.targeting import select_aggro_target

        if not await self.consume_ultimate(actor):
            return False

        from autofighter.stats import BUS  # Import here to avoid circular imports

        registry = PassiveRegistry()

        # Trigger ultimate_used for all passives (including tier Luna variants)
        # Tier multipliers will apply naturally (glitched: 128, prime: 320, etc.)
        await registry.trigger("ultimate_used", actor, party=allies, foes=enemies)

        base = actor.atk // 64
        remainder = actor.atk % 64
        for i in range(64):
            try:
                _, target = select_aggro_target(enemies)
            except ValueError:
                break
            dmg = base + (1 if i < remainder else 0)
            await target.apply_damage(dmg, attacker=actor, action_name="Generic Ultimate")
            await pace_per_target(actor)
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

        return True

    @classmethod
    def get_ultimate_description(cls) -> str:
        return (
            "Splits the user's attack into 64 rapid strikes on a single target, "
            "counting each hit as a separate action. The strike cadence follows "
            "TURN_PACING via the battle pacing helper."
        )
