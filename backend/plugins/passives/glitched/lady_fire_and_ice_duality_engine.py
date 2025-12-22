from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterable

from autofighter.effects import HealingOverTime
from autofighter.stat_effect import StatEffect
from plugins.passives.normal.lady_fire_and_ice_duality_engine import (
    LadyFireAndIceDualityEngine,
)

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class LadyFireAndIceDualityEngineGlitched(LadyFireAndIceDualityEngine):
    """[GLITCHED] Lady Fire and Ice's Duality Engine - doubled flux stacks.

    This glitched variant doubles the benefit from Elemental Flux stacks when
    alternating between fire and ice elements, providing much stronger party
    buffs and enemy debuffs.
    """
    plugin_type = "passive"
    id = "lady_fire_and_ice_duality_engine_glitched"
    name = "Glitched Duality Engine"
    trigger = "action_taken"
    max_stacks = 1
    stack_display = "spinner"

    async def _gain_flux_stack(self, target: "Stats") -> None:
        """Gain flux stack with DOUBLED potency bonus."""
        entity_id = id(target)
        self._flux_stacks[entity_id] += 1

        # DOUBLED: 10% boost per stack instead of 5%
        current_stacks = self._flux_stacks[entity_id]
        potency_bonus = current_stacks * 0.10  # Was 0.05

        flux_effect = StatEffect(
            name=f"{self.id}_flux_potency",
            stat_modifiers={
                "burn_potency": potency_bonus,
                "chill_potency": potency_bonus,
            },
            duration=-1,
            source=self.id,
        )
        target.add_effect(flux_effect)

    async def _consume_flux_stacks(
        self,
        target: "Stats",
        foes: Iterable["Stats"] | None = None,
    ) -> None:
        """Consume flux stacks with DOUBLED effects."""
        entity_id = id(target)
        stacks_to_consume = self._flux_stacks[entity_id]

        if stacks_to_consume > 0:
            # DOUBLED: 20 HP per stack instead of 10
            ally_hot_amount = max(1, stacks_to_consume * 20)  # Was 10

            hot = HealingOverTime(
                name="Glitched Duality Engine Flux",
                healing=ally_hot_amount,
                turns=3,
                id=f"{self.id}_hot_{entity_id}",
                source=target,
            )

            mgr = getattr(target, "effect_manager", None)
            if mgr is None:
                from autofighter.effects import EffectManager

                mgr = EffectManager(target)
                target.effect_manager = mgr

            await mgr.add_hot(hot)

            if foes:
                # DOUBLED: 4% mitigation reduction instead of 2%
                mitigation_reduction = stacks_to_consume * 0.04  # Was 0.02
                for foe in foes:
                    debuff = StatEffect(
                        name=f"{self.id}_flux_debuff",
                        stat_modifiers={"mitigation": -mitigation_reduction},
                        duration=2,
                        source=self.id,
                    )
                    foe.add_effect(debuff)

            self._flux_stacks[entity_id] = 0
            target.remove_effect_by_name(f"{self.id}_flux_potency")

    @classmethod
    def get_description(cls) -> str:
        return (
            "[GLITCHED] Alternating between Fire and Ice builds Elemental Flux stacks (doubled benefits). "
            "Fire applies DoTs, Ice provides defensive bonuses. "
            "High flux stacks enhance both elements significantly."
        )
