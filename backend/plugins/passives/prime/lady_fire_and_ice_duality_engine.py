from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import Iterable

from autofighter.effects import HealingOverTime
from autofighter.stat_effect import StatEffect
from plugins.passives.normal.lady_fire_and_ice_duality_engine import LadyFireAndIceDualityEngine

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class LadyFireAndIceDualityEnginePrime(LadyFireAndIceDualityEngine):
    """[PRIME] Duality Engine with hotter burns, deeper chills, and richer consumes."""

    plugin_type = "passive"
    id = "lady_fire_and_ice_duality_engine_prime"
    name = "Prime Duality Engine"
    trigger = "action_taken"
    max_stacks = 1
    stack_display = "spinner"

    async def _gain_flux_stack(self, target: "Stats") -> None:
        entity_id = id(target)
        self._flux_stacks[entity_id] += 1
        current_stacks = self._flux_stacks[entity_id]
        potency_bonus = current_stacks * 0.1

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
        entity_id = id(target)
        stacks_to_consume = self._flux_stacks[entity_id]

        if stacks_to_consume > 0:
            ally_hot_amount = max(1, stacks_to_consume * 20)
            hot = HealingOverTime(
                name="Prime Duality Engine Flux",
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
                mitigation_reduction = stacks_to_consume * 0.03
                for foe in foes:
                    debuff = StatEffect(
                        name=f"{self.id}_flux_enemy_mitigation",
                        stat_modifiers={"mitigation": -mitigation_reduction},
                        duration=3,
                        source=self.id,
                    )
                    foe.add_effect(debuff)

            target.remove_effect_by_name(f"{self.id}_flux_potency")
            self._flux_stacks[entity_id] = 0

    @classmethod
    def get_description(cls) -> str:
        return (
            "[PRIME] Alternating fire/ice builds Flux twice as fast, boosting burn and chill by 10% per stack. "
            "Matching elements consume stacks to heal 20 HP per stack over 3 turns and reduce foe mitigation by 3% per stack."
        )

