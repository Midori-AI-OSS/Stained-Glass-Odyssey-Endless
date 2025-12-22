from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import Optional

from autofighter.effects import DamageOverTime
from autofighter.effects import HealingOverTime
from autofighter.stat_effect import StatEffect
from plugins.passives.normal.lady_of_fire_infernal_momentum import LadyOfFireInfernalMomentum

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class LadyOfFireInfernalMomentumGlitched(LadyOfFireInfernalMomentum):
    """[GLITCHED] Lady of Fire's Infernal Momentum - doubled missing HP bonus.

    This glitched variant doubles the fire damage bonus from missing HP,
    making low-health burns and counters significantly more devastating.
    """
    plugin_type = "passive"
    id = "lady_of_fire_infernal_momentum_glitched"
    name = "Glitched Infernal Momentum"
    trigger = "damage_taken"
    max_stacks = 1
    stack_display = "spinner"

    async def apply(
        self,
        target: "Stats",
        attacker: Optional["Stats"] = None,
        damage: int = 0,
    ) -> None:
        """Apply Infernal Momentum with DOUBLED fire bonus."""
        # DOUBLED: 120% instead of 60%
        missing_hp_ratio = 1.0 - (target.hp / target.max_hp)
        doubled_fire_bonus = missing_hp_ratio * 1.2  # Was 0.6

        fire_bonus_effect = StatEffect(
            name=f"{self.id}_doubled_fire_bonus",
            stat_modifiers={"atk": int(target.atk * doubled_fire_bonus)},
            duration=1,
            source=self.id,
        )
        target.add_effect(fire_bonus_effect)

        if attacker is not None:
            await self.counter_attack(target, attacker, damage)
        elif damage > 0:
            await self.on_self_damage(target, damage)

    async def counter_attack(self, target: "Stats", attacker: "Stats", damage: int) -> None:
        """Apply DOUBLED burn DoT to attacker."""
        # DOUBLED: 50% of damage instead of 25%
        burn_damage = max(1, int(damage * 0.50))  # Was 0.25

        burn_dot = DamageOverTime(
            name="Glitched Infernal Momentum Burn",
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
        """Grant DOUBLED HoT when taking self-damage."""
        # DOUBLED: 100% of self-damage instead of 50%
        hot_amount = max(1, self_damage)  # Was int(self_damage * 0.5)

        hot = HealingOverTime(
            name="Glitched Infernal Momentum Regen",
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
            "[GLITCHED] Doubles Fire's missing HP damage bonus to 120% (doubled). "
            "Taking damage burns attackers for 50% of damage dealt (doubled) and self-inflicted Fire damage "
            "grants a HoT worth 100% of that damage (doubled) for two turns."
        )
