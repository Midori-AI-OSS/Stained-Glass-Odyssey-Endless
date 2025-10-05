from dataclasses import dataclass

from autofighter.effects import DamageOverTime
from autofighter.stats import Stats
from plugins import damage_effects
from plugins.damage_types._base import DamageTypeBase


@dataclass
class Ice(DamageTypeBase):
    """Control element that chills foes and slows their actions."""
    id: str = "Ice"
    weakness: str = "Fire"
    color: tuple[int, int, int] = (0, 255, 255)

    def create_dot(self, damage: float, source) -> DamageOverTime | None:
        return damage_effects.create_dot(self.id, damage, source)

    async def ultimate(
        self,
        actor: Stats,
        allies: list[Stats],
        enemies: list[Stats],
    ) -> bool:
        """Strike all foes six times, ramping damage by 30% per target."""
        from autofighter.rooms.battle.pacing import YIELD_MULTIPLIER
        from autofighter.rooms.battle.pacing import pace_sleep

        if not await self.consume_ultimate(actor):
            return False

        if not enemies:
            return True

        base = actor.atk
        for _ in range(6):
            bonus = 1.0
            for enemy in enemies:
                dmg = int(base * bonus)
                await enemy.apply_damage(
                    dmg,
                    attacker=actor,
                    action_name="Ice Ultimate",
                )
                await pace_sleep(YIELD_MULTIPLIER)
                bonus += 0.3
            await pace_sleep(YIELD_MULTIPLIER)
        return True

    @classmethod
    def get_ultimate_description(cls) -> str:
        return (
            "Strikes all foes six times in succession. Each hit within a wave "
            "deals 30% more damage than the previous target. Hits are paced via "
            "the TURN_PACING-aware helper."
        )
