from dataclasses import dataclass
import random
from typing import TYPE_CHECKING

from autofighter.effects import HealingOverTime
from autofighter.stat_effect import StatEffect
from plugins.passives.normal.kboshi_flux_cycle import KboshiFluxCycle

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class KboshiFluxCycleBoss(KboshiFluxCycle):
    """Boss Flux Cycle that stacks faster when elements fail to rotate."""

    plugin_type = "passive"
    id = "kboshi_flux_cycle_boss"
    name = "Flux Cycle (Boss)"
    trigger = "turn_start"
    stack_display = "pips"

    async def apply(self, target: "Stats") -> None:
        """Switch elements or stockpile 30% attack/7.5% HoTs per miss."""

        entity_id = id(target)
        if entity_id not in self._damage_stacks:
            self._damage_stacks[entity_id] = 0
            self._hot_stacks[entity_id] = 0

        if random.random() < 0.8:
            current_type_id = getattr(target.damage_type, "id", "Dark")
            available_types = [dt for dt in self._damage_types if dt().id != current_type_id]
            if not available_types:
                available_types = self._damage_types

            new_damage_type = random.choice(available_types)()
            target.damage_type = new_damage_type

            if self._damage_stacks[entity_id] > 0 or self._hot_stacks[entity_id] > 0:
                stacks = self._damage_stacks[entity_id]
                target.remove_effect_by_source(self.id)
                if hasattr(target, "effect_manager") and target.effect_manager:
                    await target.effect_manager.remove_hots(
                        lambda hot: hot.id.startswith(f"{self.id}_hot_{entity_id}")
                    )

                self._damage_stacks[entity_id] = 0
                self._hot_stacks[entity_id] = 0

                if stacks > 0:
                    mitigation = stacks * -0.03
                    for foe in getattr(target, "enemies", []):
                        debuff = StatEffect(
                            name=f"{self.id}_mitigation_debuff",
                            stat_modifiers={"mitigation": mitigation},
                            duration=1,
                            source=self.id,
                        )
                        foe.add_effect(debuff)
            return

        self._damage_stacks[entity_id] += 1
        self._hot_stacks[entity_id] += 1

        base_attack = (
            int(target.get_base_stat("atk"))
            if hasattr(target, "get_base_stat")
            else int(getattr(target, "_base_atk", target.atk))
        )
        bonus_amount = max(1, int(base_attack * 0.3))
        damage_bonus = StatEffect(
            name=f"{self.id}_damage_bonus_{self._damage_stacks[entity_id]}",
            stat_modifiers={"atk": bonus_amount},
            duration=-1,
            source=self.id,
        )
        target.add_effect(damage_bonus)

        heal_amount = max(1, int(target.max_hp * 0.075 * self._hot_stacks[entity_id]))
        hot = HealingOverTime(
            name="Boss Flux Cycle HoT",
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
            "[BOSS] 80% chance to rotate to a new element each turn. Failing to switch grants +30% attack and a 7.5% max HP HoT per stack; switching clears stacks and applies -3% mitigation per stack to foes."
        )
