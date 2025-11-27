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
        """Strike all foes six times, ramping damage by 30% per target.

        Deprecated wrapper that now routes through the Ice ultimate action.
        """

        from plugins.actions.ultimate.ice_ultimate import IceUltimate
        from plugins.actions.ultimate.utils import run_ultimate_action

        result = await run_ultimate_action(IceUltimate, actor, allies, enemies)
        return bool(getattr(result, "success", False))

    @classmethod
    def get_ultimate_description(cls) -> str:
        return (
            "Strikes all foes six times in succession. Each hit within a wave "
            "deals 30% more damage than the previous target. Hits are paced via "
            "the TURN_PACING-aware helper."
        )
