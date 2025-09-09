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

    async def ultimate(self, user: Stats, foes: list[Stats]) -> bool:
        """Strike all foes six times, ramping damage by 30% per target."""
        if not getattr(user, "use_ultimate", lambda: False)():
            return False
        base = user.atk
        for _ in range(6):
            bonus = 1.0
            for foe in foes:
                dmg = int(base * bonus)
                await foe.apply_damage(dmg, attacker=user, action_name="Ice Ultimate")
                bonus += 0.3
        return True
