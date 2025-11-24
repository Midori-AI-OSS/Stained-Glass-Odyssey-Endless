from dataclasses import dataclass
from typing import TYPE_CHECKING

from plugins.passives.normal.carly_guardians_aegis import CarlyGuardiansAegis

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class CarlyGuardiansAegisBoss(CarlyGuardiansAegis):
    """Boss Guardian's Aegis with sturdier heals and mitigation pacing."""

    plugin_type = "passive"
    id = "carly_guardians_aegis_boss"
    name = "Guardian's Aegis (Boss)"
    trigger = "turn_start"
    max_stacks = 50
    stack_display = "number"

    async def apply(self, target: "Stats", party=None, **_: object) -> None:
        """Run base logic but heal for 15% of defense each turn."""

        from typing import Optional

        from autofighter.stat_effect import StatEffect

        entity_id = id(target)
        if entity_id not in self._mitigation_stacks:
            self._mitigation_stacks[entity_id] = 0
        if entity_id not in self._attack_baseline:
            self._attack_baseline[entity_id] = int(target.get_base_stat("atk"))
        if entity_id not in self._defense_stacks:
            self._defense_stacks[entity_id] = 0
        if entity_id not in self._overcharged:
            self._overcharged[entity_id] = False

        if self._overcharged[entity_id]:
            self._mitigation_stacks[entity_id] = max(0, self._mitigation_stacks[entity_id] - 5)
            if self._mitigation_stacks[entity_id] <= 10:
                self._overcharged[entity_id] = False
                target.remove_effect_by_name(f"{self.id}_overcharged_atk")
            else:
                target.remove_effect_by_name(f"{self.id}_overcharged_atk")
                overcharge_effect = StatEffect(
                    name=f"{self.id}_overcharged_atk",
                    stat_modifiers={"atk": target.defense},
                    duration=-1,
                    source=self.id,
                )
                target.add_effect(overcharge_effect)

        base_atk = self._attack_baseline[entity_id]
        current_atk = int(target.get_base_stat("atk"))
        growth = current_atk - base_atk
        if growth > 0:
            self._defense_stacks[entity_id] += growth
            target.set_base_stat("atk", base_atk)

            stacks = self._defense_stacks[entity_id]
            base_defense = min(stacks, 50)
            excess_stacks = max(0, stacks - 50)
            defense_bonus = base_defense + excess_stacks * 0.5

            defense_effect = StatEffect(
                name=f"{self.id}_defense_stacks",
                stat_modifiers={"defense": defense_bonus},
                duration=-1,
                source=self.id,
            )
            target.add_effect(defense_effect)

        defense_based_heal = int(target.defense * 0.15)
        injured: Optional["Stats"] = None
        if party:
            injured = min(
                (a for a in party if a.hp < a.max_hp),
                key=lambda a: a.hp / a.max_hp,
                default=None,
            )
        recipient = injured if injured is not None else target

        await recipient.apply_healing(defense_based_heal, healer=target)

        heal_effect = StatEffect(
            name=f"{self.id}_defense_heal",
            stat_modifiers={"hp": defense_based_heal},
            duration=1,
            source=self.id,
        )
        recipient.add_effect(heal_effect)

        if self._mitigation_stacks[entity_id] > 0:
            current_stacks = self._mitigation_stacks[entity_id]
            base_mitigation = min(current_stacks, 50) * 0.02
            excess_stacks = max(0, current_stacks - 50)
            excess_mitigation = excess_stacks * 0.01
            total_mitigation = base_mitigation + excess_mitigation

            mitigation_effect = StatEffect(
                name=f"{self.id}_mitigation_stacks",
                stat_modifiers={"mitigation": total_mitigation},
                duration=-1,
                source=self.id,
            )
            target.add_effect(mitigation_effect)

    @classmethod
    def get_description(cls) -> str:
        return (
            "[BOSS] Guardian's Aegis heals 15% of Carly's defense each turn while keeping mitigation stacks, overcharge, and ally sharing intact."
        )
