from dataclasses import dataclass
import random

from autofighter.effects import DamageOverTime
from autofighter.stats import BUS
from autofighter.stats import Stats
from plugins import damage_effects
from plugins.damage_types._base import DamageTypeBase


@dataclass
class Dark(DamageTypeBase):
    """Selfish element that drains allies to fuel overwhelming strikes."""
    id: str = "Dark"
    weakness: str = "Light"
    color: tuple[int, int, int] = (145, 0, 145)

    async def on_action(self, actor, allies, enemies) -> bool:
        from autofighter.rooms.battle.pacing import YIELD_MULTIPLIER
        from autofighter.rooms.battle.pacing import pace_sleep

        total_drained = 0

        for member in allies:
            if getattr(member, "hp", 0) <= 1:
                await pace_sleep(YIELD_MULTIPLIER)
                continue

            drain = max(int(member.hp * 0.10), 1)
            drain = min(drain, member.hp - 1)
            if drain <= 0:
                await pace_sleep(YIELD_MULTIPLIER)
                continue

            drained = await member.apply_cost_damage(drain)
            total_drained += max(int(drained), 0)
            await pace_sleep(YIELD_MULTIPLIER)

        if total_drained > 0:
            variance = random.uniform(0.99, 1.01)
            bonus = 1.0 + (total_drained * 0.0001 * variance)
            setattr(actor, "_pending_dark_bonus", bonus)
        else:
            if hasattr(actor, "_pending_dark_bonus"):
                delattr(actor, "_pending_dark_bonus")

        return True

    def on_damage(self, damage, attacker, target) -> float:
        bonus = getattr(attacker, "_pending_dark_bonus", None)
        if isinstance(bonus, (int, float)) and bonus > 0:
            damage *= bonus
            try:
                delattr(attacker, "_pending_dark_bonus")
            except AttributeError:
                pass
        return damage

    # Per-stack damage multiplier for Darkness ultimate.
    # Previously 1.75, which caused extreme exponential scaling.
    # Adjust this value to tune balance without changing code below.
    ULT_PER_STACK: float = 1.005

    async def ultimate(
        self,
        actor: Stats,
        allies: list[Stats],
        enemies: list[Stats],
    ) -> bool:
        """Strike a foe six times, scaling with allied DoT stacks."""

        from autofighter.rooms.battle.pacing import YIELD_MULTIPLIER
        from autofighter.rooms.battle.pacing import pace_sleep

        if not getattr(actor, "use_ultimate", lambda: False)():
            return False
        if not enemies:
            return False

        stacks = 0
        for member in allies:
            mgr = getattr(member, "effect_manager", None)
            if mgr is not None:
                stacks += len(getattr(mgr, "dots", []))
            else:
                stacks += len(getattr(member, "dots", []))

        multiplier = self.ULT_PER_STACK ** stacks
        dmg = int(actor.atk * multiplier)
        target = enemies[0]
        for _ in range(6):
            dealt = await target.apply_damage(dmg, attacker=actor, action_name="Dark Ultimate")
            await pace_sleep(YIELD_MULTIPLIER)
            await BUS.emit_async("damage", actor, target, dealt)
        return True

    def create_dot(self, damage: float, source) -> DamageOverTime | None:
        return damage_effects.create_dot(self.id, damage, source)

    @classmethod
    def get_ultimate_description(cls) -> str:
        return (
            "Multiplies the user's attack by `ULT_PER_STACK` for each DoT stack on allied "
            "targets, then deals that damage to one enemy six times, emitting a 'damage' "
            "event after each hit. Each strike yields via TURN_PACING-aware pacing."
        )
