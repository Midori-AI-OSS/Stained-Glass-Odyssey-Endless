from dataclasses import dataclass
from typing import TYPE_CHECKING

from autofighter.stat_effect import StatEffect
from plugins.passives.normal.lady_light_radiant_aegis import LadyLightRadiantAegis

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class LadyLightRadiantAegisPrime(LadyLightRadiantAegis):
    """[PRIME] Radiant Aegis with bigger shields and cleanse rewards."""

    plugin_type = "passive"
    id = "lady_light_radiant_aegis_prime"
    name = "Prime Radiant Aegis"
    trigger = "action_taken"
    max_stacks = 1
    stack_display = "spinner"

    async def on_hot_applied(self, target: "Stats", healed_ally: "Stats", hot_amount: int) -> None:
        shield_amount = int(hot_amount * 0.75)
        if shield_amount > 0:
            if not healed_ally.overheal_enabled:
                healed_ally.enable_overheal()
            healed_ally.shields += shield_amount

        resistance_effect = StatEffect(
            name=f"{self.id}_hot_resistance",
            stat_modifiers={
                "effect_resistance": 0.08,
                "mitigation": 0.05,
            },
            duration=2,
            source=self.id,
        )
        healed_ally.add_effect(resistance_effect)

    async def on_dot_cleanse(self, target: "Stats", cleansed_ally: "Stats") -> None:
        entity_id = id(target)
        additional_healing = int(cleansed_ally.max_hp * 0.08)
        if additional_healing > 0:
            await cleansed_ally.apply_healing(
                additional_healing,
                healer=target,
                source_type="cleanse",
                source_name=self.id,
            )

        attack_increase = int(target.atk * 0.03)
        self._attack_bonuses[entity_id] = self._attack_bonuses.get(entity_id, 0) + attack_increase

        cleanse_bonus_effect = StatEffect(
            name=f"{self.id}_cleanse_attack_{entity_id}",
            stat_modifiers={
                "atk": self._attack_bonuses[entity_id],
                "regain": max(1, int(target.max_hp * 0.01)),
            },
            duration=-1,
            source=self.id,
        )
        target.add_effect(cleanse_bonus_effect)

    @classmethod
    def get_description(cls) -> str:
        return (
            "[PRIME] HoTs grant 75% of their heal as shields plus mitigation and resistance for two turns. "
            "Cleansing DoTs heals 8% max HP and builds stacking attack and regen for Lady Light."
        )

