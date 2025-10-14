from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import Optional

from autofighter.effects import DamageOverTime
from autofighter.effects import HealingOverTime
from autofighter.stat_effect import StatEffect

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class LadyOfFireInfernalMomentum:
    """Lady of Fire's Infernal Momentum passive - doubled fire damage bonus and burn mechanics."""
    plugin_type = "passive"
    id = "lady_of_fire_infernal_momentum"
    name = "Infernal Momentum"
    trigger = "damage_taken"  # Triggers when Lady of Fire takes damage
    max_stacks = 1  # Only one instance per character
    stack_display = "spinner"

    async def apply(
        self,
        target: "Stats",
        attacker: Optional["Stats"] = None,
        damage: int = 0,
    ) -> None:
        """Apply Lady of Fire's Infernal Momentum mechanics."""
        # Double the Fire damage type's missing HP damage bonus
        # This would need integration with the Fire damage type system
        # For now, apply a general damage bonus based on missing HP
        missing_hp_ratio = 1.0 - (target.hp / target.max_hp)
        doubled_fire_bonus = missing_hp_ratio * 0.6  # Assuming Fire normally gives 30%, now 60%

        fire_bonus_effect = StatEffect(
            name=f"{self.id}_doubled_fire_bonus",
            stat_modifiers={"atk": int(target.atk * doubled_fire_bonus)},
            duration=1,  # For this turn
            source=self.id,
        )
        target.add_effect(fire_bonus_effect)

        if attacker is not None:
            await self.counter_attack(target, attacker, damage)

    async def counter_attack(self, target: "Stats", attacker: "Stats", damage: int) -> None:
        """Apply burn DoT to attacker when Lady of Fire takes damage."""
        # Apply a short burn DoT to the attacker
        burn_damage = max(1, int(damage * 0.25))  # 25% of damage taken as burn

        # Use proper DoT system
        burn_dot = DamageOverTime(
            name="Infernal Momentum Burn",
            damage=burn_damage,
            turns=1,
            id=f"{self.id}_burn_{id(attacker)}",
            source=target,
        )

        # Apply DoT through effect manager if available
        if hasattr(attacker, "effect_manager") and attacker.effect_manager:
            await attacker.effect_manager.add_dot(burn_dot)
        else:
            # Fallback: create effect manager if needed
            from autofighter.effects import EffectManager
            if not hasattr(attacker, "effect_manager"):
                attacker.effect_manager = EffectManager(attacker)
            await attacker.effect_manager.add_dot(burn_dot)

        try:
            from autofighter.rooms.battle.pacing import impact_pause as _impact_pause
        except ModuleNotFoundError:
            _impact_pause = None

        if _impact_pause is not None:
            await _impact_pause(target, 1)

    async def on_self_damage(self, target: "Stats", self_damage: int) -> None:
        """Grant HoT when taking self-damage from Fire drain."""
        # Apply HoT equal to half the self-damage for two turns
        hot_amount = max(1, int(self_damage * 0.5))

        hot = HealingOverTime(
            name="Infernal Momentum Regen",
            healing=hot_amount,
            turns=2,
            id=f"{self.id}_hot_{id(target)}",
            source=target,
        )

        # Apply HoT through effect manager if available
        if hasattr(target, "effect_manager") and target.effect_manager:
            await target.effect_manager.add_hot(hot)
        else:
            # Fallback: create effect manager if needed
            from autofighter.effects import EffectManager
            if not hasattr(target, "effect_manager"):
                target.effect_manager = EffectManager(target)
            await target.effect_manager.add_hot(hot)

    @classmethod
    def get_description(cls) -> str:
        return (
            "Doubles the Fire missing HP damage bonus to 60%. "
            "Taking damage burns attackers for 25% of damage dealt and self-inflicted Fire damage grants a HoT worth 50% of that damage for two turns."
        )
