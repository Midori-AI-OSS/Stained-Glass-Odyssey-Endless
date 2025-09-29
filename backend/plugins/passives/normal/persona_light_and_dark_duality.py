from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import ClassVar

from autofighter.stat_effect import StatEffect
from plugins.damage_types import load_damage_type

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class PersonaLightAndDarkDuality:
    """Tank-focused duality for Persona Light and Dark.

    The guardian alternates between a luminous shield stance and a shadow bastion,
    dragging enemy focus to himself so his sisters stay standing.
    """

    plugin_type = "passive"
    id = "persona_light_and_dark_duality"
    name = "Twin Bastion Cycle"
    trigger = ["turn_start", "action_taken"]
    max_stacks = 5
    stack_display = "pips"

    _persona_state: ClassVar[dict[int, str]] = {}
    _stance_rank: ClassVar[dict[int, int]] = {}
    _flip_counts: ClassVar[dict[int, int]] = {}

    async def apply(self, target: "Stats", **kwargs) -> None:
        allies = self._extract_group(kwargs.get("party"))
        foes = self._extract_group(kwargs.get("foes") or kwargs.get("targets"))
        event = (kwargs.get("event") or "").lower()
        entity_id = id(target)
        observed = self._determine_persona(target)

        if entity_id not in self._persona_state:
            self._persona_state[entity_id] = observed
            self._stance_rank[entity_id] = 1
            self._flip_counts[entity_id] = 0
            self._refresh_form(target, observed, allies, foes)
            if event in ("", "turn_start"):
                await self._apply_turn_start_aura(target, observed, allies, foes)
            return

        if observed != self._persona_state[entity_id]:
            await self._handle_flip(target, observed, allies, foes)
            return

        if event in ("", "turn_start"):
            await self._apply_turn_start_aura(target, observed, allies, foes)

    async def on_action_taken(self, target: "Stats", **kwargs) -> None:
        allies = self._extract_group(kwargs.get("party"))
        foes = self._extract_group(kwargs.get("foes") or kwargs.get("targets"))
        entity_id = id(target)
        current = self._persona_state.get(entity_id) or self._determine_persona(target)
        new_persona = "light" if current == "dark" else "dark"
        target.damage_type = load_damage_type(new_persona.title())
        await self._handle_flip(target, new_persona, allies, foes)

    async def _handle_flip(
        self,
        target: "Stats",
        new_persona: str,
        allies: list["Stats"],
        foes: list["Stats"],
    ) -> None:
        entity_id = id(target)
        flips = self._flip_counts.get(entity_id, 0) + 1
        self._flip_counts[entity_id] = flips
        rank = self._stance_rank.get(entity_id, 1)
        rank = min(rank + 1, 6)
        self._stance_rank[entity_id] = rank
        self._persona_state[entity_id] = new_persona

        self._refresh_form(target, new_persona, allies, foes)

        if new_persona == "light":
            await self._apply_light_entry(target, allies, rank)
        else:
            await self._apply_dark_entry(target, allies, foes, rank)

    def _refresh_form(
        self,
        target: "Stats",
        persona: str,
        allies: list["Stats"],
        foes: list["Stats"],
    ) -> None:
        self._clear_effects(target, allies, foes)
        if persona == "light":
            self._apply_light_form(target, allies)
        else:
            self._apply_dark_form(target, allies, foes)

    def _apply_light_form(self, target: "Stats", allies: list["Stats"]) -> None:
        rank = self._stance_rank.get(id(target), 1)
        base_defense = self._get_base_value(target, "defense")
        defense_bonus = int(base_defense * (0.10 + 0.02 * (rank - 1)))
        mitigation_bonus = 0.05 + 0.01 * (rank - 1)
        resistance_bonus = 0.06 + 0.01 * (rank - 1)
        regain_bonus = 20 + 5 * (rank - 1)

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

        ally_mitigation = 0.03 + 0.005 * (rank - 1)
        ally_resistance = 0.03 + 0.005 * (rank - 1)
        ally_regain = 10 * rank
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
        max_hp_bonus = int(base_max_hp * (0.08 + 0.02 * (rank - 1)))
        defense_bonus = int(base_defense * (0.18 + 0.04 * (rank - 1)))
        mitigation_bonus = 0.07 + 0.015 * (rank - 1)
        aggro_bonus = 2.5 + 0.5 * (rank - 1)

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

        ally_guard = 0.02 + 0.005 * (rank - 1)
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

        debuff_crit = -0.03 * rank
        debuff_effect = -0.04 * rank
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
            pulse_value = 12 * rank
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
            ward_defense = int(base_defense * (0.05 + 0.01 * (rank - 1)))
            ward_mitigation = 0.025 + 0.005 * (rank - 1)
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
                        stat_modifiers={"crit_rate": -0.02 * rank},
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
        heal_amount = max(int(target.max_hp * (0.03 + 0.01 * (rank - 1))), 25)
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
        guard_value = 0.03 + 0.01 * (rank - 1)
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

        suppression = -0.03 * rank
        for foe in foes:
            foe.add_effect(
                StatEffect(
                    name=f"{self.id}_dark_suppression",
                    stat_modifiers={"effect_hit_rate": suppression},
                    duration=2,
                    source=self.id,
                )
            )

    def _clear_effects(
        self,
        target: "Stats",
        allies: list["Stats"],
        foes: list["Stats"],
    ) -> None:
        target.remove_effect_by_source(self.id)
        for collection in (allies, foes):
            for entity in collection:
                entity.remove_effect_by_source(self.id)

    def _determine_persona(self, target: "Stats") -> str:
        element = getattr(getattr(target, "damage_type", None), "id", "").lower()
        if "light" in element:
            return "light"
        if "dark" in element:
            return "dark"
        return "light"

    def _extract_group(self, value: object | None) -> list["Stats"]:
        if value is None:
            return []
        if hasattr(value, "members"):
            members = getattr(value, "members")
            return [m for m in members if m is not None]
        if isinstance(value, (list, tuple, set)):
            return [m for m in value if m is not None]
        return []

    def _get_base_value(self, target: "Stats", stat: str) -> float:
        attr = f"_base_{stat}"
        if hasattr(target, attr):
            value = getattr(target, attr)
            if isinstance(value, (int, float)):
                return float(value)
        try:
            base_value = target.get_base_stat(stat)
            if isinstance(base_value, (int, float)):
                return float(base_value)
        except Exception:
            pass
        fallback = getattr(target, stat, 0)
        try:
            return float(fallback)
        except Exception:
            return 0.0

    @classmethod
    def get_stacks(cls, target: "Stats") -> dict[str, int | str | None]:
        entity_id = id(target)
        rank = cls._stance_rank.get(entity_id, 1)
        persona = cls._persona_state.get(entity_id)
        return {
            "count": min(rank, 3),
            "rank": rank,
            "persona": persona,
            "flips": cls._flip_counts.get(entity_id, 0),
        }

    @classmethod
    def get_persona(cls, target: "Stats") -> str | None:
        return cls._persona_state.get(id(target))

    @classmethod
    def get_flip_count(cls, target: "Stats") -> int:
        return cls._flip_counts.get(id(target), 0)

    @classmethod
    def get_description(cls) -> str:
        return (
            "Opens combat in either Light or Dark stance and flips personas after each action. "
            "Light stance bolsters defense, mitigation, and regen pulses while healing the party on entry. "
            "Dark stance swells his max HP, aggro, and ally cover while blinding foes to keep pressure on him."
        )
