from dataclasses import dataclass
from typing import TYPE_CHECKING

from plugins.passives.normal.hilander_critical_ferment import HilanderCriticalFerment

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class HilanderCriticalFermentGlitched(HilanderCriticalFerment):
    """[GLITCHED] Hilander's Critical Ferment - doubled crit bonuses.

    This glitched variant doubles the crit rate (+10% instead of +5%) and crit damage
    (+20% instead of +10%) per stack, leading to much faster critical hit potential
    while maintaining the same consumption and Aftertaste mechanics.
    """
    plugin_type = "passive"
    id = "hilander_critical_ferment_glitched"
    name = "Glitched Critical Ferment"
    trigger = "hit_landed"
    stack_display = "pips"

    async def apply(
        self,
        attacker: "Stats",
        hit_target=None,
        damage=None,
        action_type=None,
        event=None,
        stack_index=None,
        **_kwargs,
    ) -> None:
        """Apply crit building mechanics with DOUBLED bonuses."""
        import random
        from weakref import ref

        from autofighter.stat_effect import StatEffect
        from autofighter.stats import BUS

        # Count existing ferment stacks
        ferment_stacks = sum(
            1
            for effect in attacker._active_effects
            if effect.name.startswith(f"{self.id}_crit_stack") and effect.name.endswith("_rate")
        )

        if ferment_stacks >= 20:
            chance = max(0.01, 1 - 0.05 * (ferment_stacks - 19))
            if random.random() >= chance:
                return

        # Add a new stack with DOUBLED bonuses
        stack_id = ferment_stacks + 1
        crit_rate_bonus = StatEffect(
            name=f"{self.id}_crit_stack_{stack_id}_rate",
            stat_modifiers={"crit_rate": 0.10},  # DOUBLED from 0.05
            duration=-1,
            source=self.id,
        )
        attacker.add_effect(crit_rate_bonus)

        crit_damage_bonus = StatEffect(
            name=f"{self.id}_crit_stack_{stack_id}_damage",
            stat_modifiers={"crit_damage": 0.20},  # DOUBLED from 0.1
            duration=-1,
            source=self.id,
        )
        attacker.add_effect(crit_damage_bonus)

        if getattr(attacker, "_hilander_crit_cb", None) is None:
            attacker_ref = ref(attacker)

            def _crit(crit_attacker, crit_target, crit_damage, *_args, **_kwargs) -> None:
                tgt = attacker_ref()
                if tgt is None:
                    BUS.unsubscribe("critical_hit", _crit)
                    return
                if crit_attacker is tgt:
                    self.on_critical_hit(tgt, crit_target, crit_damage)

            BUS.subscribe("critical_hit", _crit)
            attacker._hilander_crit_cb = _crit
        return None

    @classmethod
    def get_description(cls) -> str:
        return (
            "[GLITCHED] Each hit grants +10% crit rate (doubled) and +20% crit damage (doubled). "
            "Beyond 20 stacks, stack gain odds drop 5% per extra stack (min 1%). "
            "A critical hit triggers Aftertaste and consumes one stack."
        )
