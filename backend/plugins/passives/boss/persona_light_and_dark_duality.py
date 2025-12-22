from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import ClassVar

from autofighter.stat_effect import StatEffect
from plugins.passives.normal.persona_light_and_dark_duality import PersonaLightAndDarkDuality

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class PersonaLightAndDarkDualityBoss(PersonaLightAndDarkDuality):
    """Boss Duality stance with 1.5× stance bonuses across light and dark."""

    plugin_type = "passive"
    id = "persona_light_and_dark_duality_boss"
    name = "Light and Dark Duality (Boss)"
    trigger = ["turn_start", "action_taken"]
    max_stacks = 5
    stack_display = "pips"

    _persona_state: ClassVar[dict[int, str]] = {}
    _stance_rank: ClassVar[dict[int, int]] = {}
    _flip_counts: ClassVar[dict[int, int]] = {}

    def _apply_light_form(self, target: "Stats", allies: list["Stats"]) -> None:
        rank = self._stance_rank.get(id(target), 1)
        base_defense = self._get_base_value(target, "defense")
        defense_bonus = int(base_defense * (0.15 + 0.03 * (rank - 1)))
        mitigation_bonus = 0.075 + 0.015 * (rank - 1)
        resistance_bonus = 0.09 + 0.015 * (rank - 1)
        regain_bonus = int(30 + 7.5 * (rank - 1))

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

        ally_mitigation = 0.045 + 0.0075 * (rank - 1)
        ally_resistance = 0.045 + 0.0075 * (rank - 1)
        ally_regain = 15 * rank
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
        max_hp_bonus = int(base_max_hp * (0.12 + 0.03 * (rank - 1)))
        defense_bonus = int(base_defense * (0.27 + 0.06 * (rank - 1)))
        mitigation_bonus = 0.105 + 0.0225 * (rank - 1)
        aggro_bonus = 3.75 + 0.75 * (rank - 1)

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

        ally_guard = 0.03 + 0.0075 * (rank - 1)
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

        debuff_crit = -0.045 * rank
        debuff_effect = -0.06 * rank
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
            pulse_value = 18 * rank
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
            ward_defense = int(base_defense * (0.075 + 0.015 * (rank - 1)))
            ward_mitigation = 0.0375 + 0.0075 * (rank - 1)
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
                        stat_modifiers={"crit_rate": -0.03 * rank},
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
        heal_amount = max(
            int(target.max_hp * (0.045 + 0.015 * (rank - 1))),
            38,
        )
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
        guard_value = 0.045 + 0.015 * (rank - 1)
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

        suppression = -0.045 * rank
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
            "[BOSS] Opens in Light or Dark stance like normal but all stance modifiers are 1.5× stronger: beefier shields/regen in Light and heavier HP/defense/aggro plus suppression in Dark."
        )
