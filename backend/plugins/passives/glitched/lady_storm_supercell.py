from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar, Iterable

from autofighter.stat_effect import StatEffect
from plugins.passives.normal.lady_storm_supercell import LadyStormSupercell

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class LadyStormSupercellGlitched(LadyStormSupercell):
    """[GLITCHED] Lady Storm's Supercell - doubled Wind/Lightning enhancements."""

    plugin_type = "passive"
    id = "lady_storm_supercell_glitched"
    name = "Glitched Supercell"
    trigger = ["turn_start", "action_taken", "hit_landed"]
    max_stacks = 1
    stack_display = "spinner"

    _storm_phase: ClassVar[dict[int, str]] = {}
    _storm_charge: ClassVar[dict[int, int]] = {}

    async def apply(
        self,
        target: "Stats",
        *,
        party: Iterable["Stats"] | None = None,
        foes: Iterable["Stats"] | None = None,
        **_: object,
    ) -> None:
        """Apply doubled Wind and Lightning baselines without altering phase flow."""

        entity_id = id(target)
        self._storm_phase.setdefault(entity_id, "wind")
        self._storm_charge.setdefault(entity_id, 0)

        base_attack = getattr(target, "_base_atk", target.atk)
        base_defense = getattr(target, "_base_defense", target.defense)

        tailwind_effect = StatEffect(
            name=f"{self.id}_tailwind_core",
            stat_modifiers={
                "spd": 16,  # Was 8, now 16
                "dodge_odds": 0.16,  # Was 0.08, now 0.16
                "aggro_modifier": -50.0,  # Was -25.0, now -50.0
            },
            duration=-1,
            source=self.id,
        )
        target.add_effect(tailwind_effect)

        storm_edge_effect = StatEffect(
            name=f"{self.id}_storm_edge",
            stat_modifiers={
                "atk": int(base_attack * 0.44),  # Was 0.22, now 0.44
                "crit_rate": 0.24,  # Was 0.12, now 0.24
                "effect_hit_rate": 0.30,  # Was 0.15, now 0.30
            },
            duration=-1,
            source=self.id,
        )
        target.add_effect(storm_edge_effect)

        storm_barrier_effect = StatEffect(
            name=f"{self.id}_storm_barrier",
            stat_modifiers={
                "mitigation": 0.24,  # Was 0.12, now 0.24
                "effect_resistance": 0.24,  # Was 0.12, now 0.24
                "defense": int(base_defense * 0.30),  # Was 0.15, now 0.30
            },
            duration=-1,
            source=self.id,
        )
        target.add_effect(storm_barrier_effect)

        await self._spread_gale(target, party)

        if foes:
            for foe in foes:
                if getattr(foe, "hp", 0) <= 0:
                    continue
                squall_marker = StatEffect(
                    name=f"{self.id}_squall_marker_{entity_id}",
                    stat_modifiers={"dodge_odds": -0.04},  # Was -0.02, now -0.04
                    duration=2,
                    source=self.id,
                )
                foe.add_effect(squall_marker)

    async def on_action_taken(self, target: "Stats", **kwargs: object) -> None:
        """Alternate phases with doubled buffs/debuffs."""

        entity_id = id(target)
        phase = self._storm_phase.get(entity_id, "wind")

        party = kwargs.get("party")
        foes = kwargs.get("foes")

        allies: list["Stats"] = []
        if party is not None:
            if hasattr(party, "members"):
                allies = [member for member in party.members if member is not target]
            else:
                allies = [member for member in party if member is not target]

        foe_list: list["Stats"] = []
        if foes is not None:
            if hasattr(foes, "members"):
                foe_list = list(foes.members)
            else:
                foe_list = list(foes)

        if phase == "wind":
            gale_effect = StatEffect(
                name=f"{self.id}_slipstream",
                stat_modifiers={"spd": 20, "dodge_odds": 0.12},  # Was 10/0.06, now doubled
                duration=2,
                source=self.id,
            )
            target.add_effect(gale_effect)

            for ally in allies:
                if getattr(ally, "hp", 0) <= 0:
                    continue
                ally_effect = StatEffect(
                    name=f"{self.id}_slipstream_ally_{entity_id}",
                    stat_modifiers={"spd": 12, "dodge_odds": 0.08},  # Was 6/0.04, now doubled
                    duration=2,
                    source=self.id,
                )
                ally.add_effect(ally_effect)

            self._storm_phase[entity_id] = "lightning"
            return

        new_charge = min(self._storm_charge.get(entity_id, 0) + 1, 3)
        self._storm_charge[entity_id] = new_charge

        surge_effect = StatEffect(
            name=f"{self.id}_voltage_field",
            stat_modifiers={
                "crit_rate": 0.10 * new_charge,  # Was 0.05 per charge, now doubled
                "crit_damage": 0.16 * new_charge,  # Was 0.08 per charge, now doubled
            },
            duration=1,
            source=self.id,
        )
        target.add_effect(surge_effect)

        for foe in foe_list:
            if getattr(foe, "hp", 0) <= 0:
                continue
            shock_effect = StatEffect(
                name=f"{self.id}_charged_vulnerability_{entity_id}",
                stat_modifiers={"mitigation": -0.08 * new_charge},  # Was -0.04, now -0.08
                duration=1,
                source=self.id,
            )
            foe.add_effect(shock_effect)

        self._storm_phase[entity_id] = "wind"

    async def on_hit_landed(
        self,
        attacker: "Stats",
        target_hit: "Stats",
        damage: int = 0,
        action_type: str = "attack",
        **_: object,
    ) -> None:
        """Detonate stored lightning charges with doubled multipliers."""

        attacker_id = id(attacker)
        charges = self._storm_charge.get(attacker_id, 0)
        if charges <= 0:
            return

        bonus_damage = max(
            int(attacker.atk * (0.60 + 0.30 * (charges - 1))),  # Was 0.3/0.15, now doubled
            charges * 150,  # Was 75 per charge, now 150
        )
        try:
            await target_hit.apply_damage(
                bonus_damage,
                attacker=attacker,
                trigger_on_hit=False,
                action_name="Supercell Surge",
            )
        except Exception:
            pass

        shock_lock = StatEffect(
            name=f"{self.id}_grounding_shock",
            stat_modifiers={
                "mitigation": -0.12 * charges,  # Was -0.06, now -0.12
                "dodge_odds": -0.04 * charges,  # Was -0.02, now -0.04
            },
            duration=2,
            source=self.id,
        )
        target_hit.add_effect(shock_lock)

        regen_effect = StatEffect(
            name=f"{self.id}_storm_regain",
            stat_modifiers={"regain": charges * 60},  # Was 30, now 60
            duration=3,
            source=self.id,
        )
        attacker.add_effect(regen_effect)

        self._storm_charge[attacker_id] = 0

    async def _spread_gale(
        self,
        target: "Stats",
        party: Iterable["Stats"] | None,
    ) -> None:
        if party is None:
            return

        if hasattr(party, "members"):
            members = party.members
        else:
            members = party

        for ally in members:
            if ally is target or getattr(ally, "hp", 0) <= 0:
                continue
            gale = StatEffect(
                name=f"{self.id}_everstorm_aura_{id(target)}",
                stat_modifiers={"spd": 8, "regain": 40},  # Was 4/20, now doubled
                duration=3,
                source=self.id,
            )
            ally.add_effect(gale)

    @classmethod
    def get_description(cls) -> str:
        return (
            "[GLITCHED] Persistent tailwinds now grant +16 SPD, +16% dodge, and -50 aggro while doubling storm edges (+44% ATK, +24% crit, +30% effect hit). "
            "Actions alternate wind slipstreams (+20 SPD/+12% dodge self, +12 SPD/+8% dodge allies) with lightning charges that stack doubled crit bonuses and -8% mitigation per charge. "
            "Charged strikes detonate for doubled surge damage and regen while heavily grounding foes."
        )
