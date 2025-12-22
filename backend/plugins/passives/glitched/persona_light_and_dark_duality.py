from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

from autofighter.stat_effect import StatEffect
from plugins.passives.normal.persona_light_and_dark_duality import (
    PersonaLightAndDarkDuality,
)

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class PersonaLightAndDarkDualityGlitched(PersonaLightAndDarkDuality):
    """[GLITCHED] Persona Light and Dark's Duality - doubled stance bonuses."""

    plugin_type = "passive"
    id = "persona_light_and_dark_duality_glitched"
    name = "Glitched Light and Dark Duality"
    trigger = ["turn_start", "action_taken"]
    max_stacks = 5
    stack_display = "pips"

    _persona_state: ClassVar[dict[int, str]] = {}
    _stance_rank: ClassVar[dict[int, int]] = {}
    _flip_counts: ClassVar[dict[int, int]] = {}

    def _apply_light_form(self, target: "Stats", allies: list["Stats"]) -> None:
        rank = self._stance_rank.get(id(target), 1)
        base_defense = self._get_base_value(target, "defense")
        defense_bonus = int(base_defense * (0.20 + 0.04 * (rank - 1)))  # Was 0.10/0.02, now doubled
        mitigation_bonus = 0.10 + 0.02 * (rank - 1)  # Was 0.05/0.01, now doubled
        resistance_bonus = 0.12 + 0.02 * (rank - 1)  # Was 0.06/0.01, now doubled
        regain_bonus = 40 + 10 * (rank - 1)  # Was 20/5, now doubled

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

        ally_mitigation = 0.06 + 0.01 * (rank - 1)  # Was 0.03/0.005, now doubled
        ally_resistance = 0.06 + 0.01 * (rank - 1)  # Was 0.03/0.005, now doubled
        ally_regain = 20 * rank  # Was 10 * rank, now doubled
        for ally in allies:
            if ally is target:
                continue
            ally.add_effect(
                StatEffect(
                    name=f"{self.id}_light_screen",
                    stat_modifiers={
                        "mitigation": ally_mitigation,
                        "effect_resistance": ally_resistance,
                        "regain": ally_regain,
                    },
                    duration=2,
                    source=self.id,
                )
            )

    def _apply_dark_form(
        self,
        target: "Stats",
        allies: list["Stats"],
        foes: list["Stats"],
    ) -> None:
        rank = self._stance_rank.get(id(target), 1)
        base_max_hp = self._get_base_value(target, "max_hp")
        base_defense = self._get_base_value(target, "defense")
        max_hp_bonus = int(base_max_hp * (0.16 + 0.04 * (rank - 1)))  # Was 0.08/0.02, now doubled
        defense_bonus = int(base_defense * (0.36 + 0.08 * (rank - 1)))  # Was 0.18/0.04, now doubled
        mitigation_bonus = 0.14 + 0.03 * (rank - 1)  # Was 0.07/0.015, now doubled
        aggro_bonus = 5.0 + 1.0 * (rank - 1)  # Was 2.5/0.5, now doubled

        target.add_effect(
            StatEffect(
                name=f"{self.id}_dark_bastion",
                stat_modifiers={
                    "max_hp": max_hp_bonus,
                    "defense": defense_bonus,
                    "mitigation": mitigation_bonus,
                    "aggro_modifier": aggro_bonus,
                },
                duration=-1,
                source=self.id,
            )
        )

        ally_guard = 0.04 + 0.01 * (rank - 1)  # Was 0.02/0.005, now doubled
        for ally in allies:
            if ally is target:
                continue
            ally.add_effect(
                StatEffect(
                    name=f"{self.id}_dark_cover",
                    stat_modifiers={"mitigation": ally_guard},
                    duration=1,
                    source=self.id,
                )
            )

        debuff_crit = -0.06 * rank  # Was -0.03 * rank, now doubled
        debuff_effect = -0.08 * rank  # Was -0.04 * rank, now doubled
        for foe in foes:
            foe.add_effect(
                StatEffect(
                    name=f"{self.id}_dark_smother",
                    stat_modifiers={
                        "crit_rate": debuff_crit,
                        "effect_hit_rate": debuff_effect,
                    },
                    duration=1,
                    source=self.id,
                )
            )

    async def _apply_turn_start_aura(
        self,
        target: "Stats",
        persona: str,
        allies: list["Stats"],
        foes: list["Stats"],
    ) -> None:
        rank = self._stance_rank.get(id(target), 1)
        if persona == "light":
            pulse_value = 24 * rank  # Was 12 * rank, now doubled
            for entity in [target, *[a for a in allies if a is not target]]:
                entity.add_effect(
                    StatEffect(
                        name=f"{self.id}_light_pulse",
                        stat_modifiers={"regain": pulse_value},
                        duration=1,
                        source=self.id,
                    )
                )
        else:
            base_defense = self._get_base_value(target, "defense")
            ward_defense = int(base_defense * (0.10 + 0.02 * (rank - 1)))  # Was 0.05/0.01, now doubled
            ward_mitigation = 0.05 + 0.01 * (rank - 1)  # Was 0.025/0.005, now doubled
            target.add_effect(
                StatEffect(
                    name=f"{self.id}_dark_ward",
                    stat_modifiers={
                        "defense": ward_defense,
                        "mitigation": ward_mitigation,
                    },
                    duration=1,
                    source=self.id,
                )
            )
            for foe in foes:
                foe.add_effect(
                    StatEffect(
                        name=f"{self.id}_dark_glare",
                        stat_modifiers={"crit_rate": -0.04 * rank},  # Was -0.02, now doubled
                        duration=1,
                        source=self.id,
                    )
                )

    async def _apply_light_entry(
        self,
        target: "Stats",
        allies: list["Stats"],
        rank: int,
    ) -> None:
        heal_amount = max(int(target.max_hp * (0.06 + 0.02 * (rank - 1))), 50)  # Was 0.03/0.01 and 25 floor, now doubled
        recipients = [target]
        recipients.extend(ally for ally in allies if ally is not target)
        for entity in recipients:
            try:
                await entity.apply_healing(
                    heal_amount,
                    healer=target,
                    source_type="passive",
                    source_name=self.id,
                )
            except Exception:
                continue

    async def _apply_dark_entry(
        self,
        target: "Stats",
        allies: list["Stats"],
        foes: list["Stats"],
        rank: int,
    ) -> None:
        guard_value = 0.06 + 0.02 * (rank - 1)  # Was 0.03/0.01, now doubled
        for ally in allies:
            if ally is target:
                continue
            ally.add_effect(
                StatEffect(
                    name=f"{self.id}_dark_guard",
                    stat_modifiers={"mitigation": guard_value},
                    duration=2,
                    source=self.id,
                )
            )

        suppression = -0.06 * rank  # Was -0.03 * rank, now doubled
        for foe in foes:
            foe.add_effect(
                StatEffect(
                    name=f"{self.id}_dark_suppression",
                    stat_modifiers={"effect_hit_rate": suppression},
                    duration=2,
                    source=self.id,
                )
            )

    @classmethod
    def get_description(cls) -> str:
        return (
            "[GLITCHED] Opens in Light or Dark stance and still flips after each action, but all stance bonuses are doubled. "
            "Light: +20%+ def scaling, +10% mitigation, +12% resist, and bigger regen pulses plus doubled entry heals. "
            "Dark: +16%+ max HP, +36%+ defense, +5 aggro scaling, stronger ally guard, and doubled suppression on foes."
        )
