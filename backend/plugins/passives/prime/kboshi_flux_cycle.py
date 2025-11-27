from dataclasses import dataclass
import random
from typing import TYPE_CHECKING

from autofighter.effects import HealingOverTime
from autofighter.stat_effect import StatEffect
from plugins.damage_types.dark import Dark
from plugins.damage_types.fire import Fire
from plugins.damage_types.ice import Ice
from plugins.damage_types.light import Light
from plugins.damage_types.lightning import Lightning
from plugins.damage_types.wind import Wind
from plugins.passives.normal.kboshi_flux_cycle import KboshiFluxCycle

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class KboshiFluxCyclePrime(KboshiFluxCycle):
    """[PRIME] Flux Cycle with heavier stacking and punishing element flips."""

    plugin_type = "passive"
    id = "kboshi_flux_cycle_prime"
    name = "Prime Flux Cycle"
    trigger = "turn_start"
    stack_display = "pips"

    _damage_types = [Fire, Ice, Wind, Lightning, Light, Dark]

    async def apply(self, target: "Stats") -> None:
        entity_id = id(target)

        if entity_id not in self._damage_stacks:
            self._damage_stacks[entity_id] = 0
            self._hot_stacks[entity_id] = 0

        if random.random() < 0.85:
            current_type_id = getattr(target.damage_type, 'id', 'Dark')
            available_types = [dt for dt in self._damage_types if dt().id != current_type_id]
            if not available_types:
                available_types = self._damage_types
            new_damage_type_class = random.choice(available_types)
            target.damage_type = new_damage_type_class()

            stacks = self._damage_stacks[entity_id]
            if stacks > 0:
                target.remove_effect_by_source(self.id)
                if hasattr(target, "effect_manager") and target.effect_manager:
                    await target.effect_manager.remove_hots(
                        lambda hot: hot.id.startswith(f"{self.id}_hot_{entity_id}")
                    )
                mitigation = stacks * -0.06
                for foe in getattr(target, "enemies", []):
                    debuff = StatEffect(
                        name=f"{self.id}_mitigation_debuff",
                        stat_modifiers={"mitigation": mitigation},
                        duration=1,
                        source=self.id,
                    )
                    foe.add_effect(debuff)
                self._damage_stacks[entity_id] = 0
                self._hot_stacks[entity_id] = 0
        else:
            self._damage_stacks[entity_id] += 1
            self._hot_stacks[entity_id] += 1

            base_attack = (
                int(target.get_base_stat("atk"))
                if hasattr(target, "get_base_stat")
                else int(getattr(target, "_base_atk", target.atk))
            )
            bonus_amount = max(1, int(base_attack * 0.6))
            damage_bonus = StatEffect(
                name=f"{self.id}_damage_bonus_{self._damage_stacks[entity_id]}",
                stat_modifiers={"atk": bonus_amount},
                duration=-1,
                source=self.id,
            )
            target.add_effect(damage_bonus)

            heal_amount = max(1, int(target.max_hp * 0.15 * self._hot_stacks[entity_id]))
            hot = HealingOverTime(
                name=f"Prime Flux Cycle HoT (Stack {self._hot_stacks[entity_id]})",
                healing=heal_amount,
                turns=1,
                id=f"{self.id}_hot_{entity_id}_{self._hot_stacks[entity_id]}",
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
            "[PRIME] 85% chance to rotate to a new element. Failure grants +60% attack and a 15% max HP HoT per stack; switching clears stacks and applies -6% mitigation to foes per stack."
        )

