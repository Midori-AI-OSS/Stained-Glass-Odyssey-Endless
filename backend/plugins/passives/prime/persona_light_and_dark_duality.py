from dataclasses import dataclass
from typing import TYPE_CHECKING

from autofighter.stat_effect import StatEffect
from plugins.passives.normal.persona_light_and_dark_duality import (
    PersonaLightAndDarkDuality,
)

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class PersonaLightAndDarkDualityPrime(PersonaLightAndDarkDuality):
    """[PRIME] Twin Bastion Cycle with higher stance ranks and flip rewards."""

    plugin_type = "passive"
    id = "persona_light_and_dark_duality_prime"
    name = "Prime Twin Bastion"
    trigger = ["turn_start", "action_taken"]
    max_stacks = 7
    stack_display = "pips"

    def _apply_light_form(self, target: "Stats", allies: list["Stats"]) -> None:
        rank = self._stance_rank.get(id(target), 1)
        base_defense = self._get_base_value(target, "defense")
        defense_bonus = int(base_defense * (0.16 + 0.03 * (rank - 1)))
        mitigation_bonus = 0.08 + 0.015 * (rank - 1)
        resistance_bonus = 0.08 + 0.015 * (rank - 1)
        regain_bonus = 30 + 8 * (rank - 1)

        target.add_effect(
            StatEffect(
                name=f"{self.id}_light_aegis",
                stat_modifiers={
                    "defense": defense_bonus,
                    "mitigation": mitigation_bonus,
                    "effect_resistance": resistance_bonus,
                    "regain": regain_bonus,
                },
                duration=-1,
                source=self.id,
            )
        )

        for ally in allies:
            ally.add_effect(
                StatEffect(
                    name=f"{self.id}_light_guard_{id(target)}",
                    stat_modifiers={"mitigation": 0.03 + 0.01 * rank},
                    duration=-1,
                    source=self.id,
                )
            )

    def _apply_dark_form(self, target: "Stats", allies: list["Stats"], foes: list["Stats"]) -> None:
        rank = self._stance_rank.get(id(target), 1)
        base_atk = self._get_base_value(target, "atk")
        attack_bonus = int(base_atk * (0.14 + 0.03 * (rank - 1)))
        crit_bonus = 0.12 + 0.02 * (rank - 1)
        aggro_bonus = 75.0 + 15.0 * (rank - 1)

        target.add_effect(
            StatEffect(
                name=f"{self.id}_dark_blades",
                stat_modifiers={
                    "atk": attack_bonus,
                    "crit_rate": crit_bonus,
                    "aggro_modifier": aggro_bonus,
                },
                duration=-1,
                source=self.id,
            )
        )

        for foe in foes:
            foe.add_effect(
                StatEffect(
                    name=f"{self.id}_dark_mark_{id(target)}",
                    stat_modifiers={"mitigation": -0.02 * rank},
                    duration=2,
                    source=self.id,
                )
            )

    async def _apply_light_entry(self, target: "Stats", allies: list["Stats"], rank: int) -> None:
        await super()._apply_light_entry(target, allies, rank)

        shield = StatEffect(
            name=f"{self.id}_light_entry_shield",
            stat_modifiers={"max_hp": int(target.max_hp * 0.05 * rank)},
            duration=2,
            source=self.id,
        )
        target.add_effect(shield)

    @classmethod
    def get_description(cls) -> str:
        return (
            "[PRIME] Light stance grants higher defense, mitigation, and party guard; dark stance scales attack and crit harder while marking foes. Flips ramp stance rank faster and add entry shields."
        )
