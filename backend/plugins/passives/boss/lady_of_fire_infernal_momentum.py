from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from autofighter.effects import DamageOverTime, HealingOverTime
from autofighter.stat_effect import StatEffect
from plugins.passives.normal.lady_of_fire_infernal_momentum import (
    LadyOfFireInfernalMomentum,
)

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class LadyOfFireInfernalMomentumBoss(LadyOfFireInfernalMomentum):
    """Boss Infernal Momentum that scales 1.5× harder off missing HP."""

    plugin_type = "passive"
    id = "lady_of_fire_infernal_momentum_boss"
    name = "Infernal Momentum (Boss)"
    trigger = "damage_taken"
    max_stacks = 1
    stack_display = "spinner"

    async def apply(
        self,
        target: "Stats",
        attacker: Optional["Stats"] = None,
        damage: int = 0,
    ) -> None:
        missing_hp_ratio = 1.0 - (target.hp / target.max_hp)
        fire_bonus = missing_hp_ratio * 0.9

        fire_bonus_effect = StatEffect(
            name=f"{self.id}_boss_fire_bonus",
            stat_modifiers={"atk": int(target.atk * fire_bonus)},
            duration=1,
            source=self.id,
        )
        target.add_effect(fire_bonus_effect)

        if attacker is not None:
            await self.counter_attack(target, attacker, damage)
        elif damage > 0:
            await self.on_self_damage(target, damage)

    async def counter_attack(self, target: "Stats", attacker: "Stats", damage: int) -> None:
        burn_damage = max(1, int(damage * 0.375))
        burn_dot = DamageOverTime(
            name="Boss Infernal Momentum Burn",
            damage=burn_damage,
            turns=1,
            id=f"{self.id}_burn_{id(attacker)}",
            source=target,
        )

        mgr = getattr(attacker, "effect_manager", None)
        if mgr is None:
            from autofighter.effects import EffectManager

            mgr = EffectManager(attacker)
            attacker.effect_manager = mgr

        await mgr.add_dot(burn_dot)

        try:
            from autofighter.rooms.battle.pacing import impact_pause as _impact_pause
        except ModuleNotFoundError:
            _impact_pause = None

        if _impact_pause is not None:
            await _impact_pause(target, 1)

    async def on_self_damage(self, target: "Stats", self_damage: int) -> None:
        hot_amount = max(1, int(self_damage * 0.75))
        hot = HealingOverTime(
            name="Boss Infernal Momentum Regen",
            healing=hot_amount,
            turns=2,
            id=f"{self.id}_hot_{id(target)}",
            source=target,
        )

        mgr = getattr(target, "effect_manager", None)
        if mgr is None:
            from autofighter.effects import EffectManager

            mgr = EffectManager(target)
            target.effect_manager = mgr

        await mgr.add_hot(hot)

    @classmethod
    def get_description(cls) -> str:
        return (
            "[BOSS] Fire bonus scales to 90% of missing HP, burns attackers for 37.5% of the damage dealt, and self-inflicted Fire damage grants a HoT worth 75% of that damage for two turns."
        )
