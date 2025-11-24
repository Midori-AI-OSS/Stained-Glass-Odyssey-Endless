from dataclasses import dataclass
from typing import TYPE_CHECKING

from autofighter.stat_effect import StatEffect
from plugins.passives.normal.ally_overload import AllyOverload

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class AllyOverloadPrime(AllyOverload):
    """[PRIME] Ally's Overload with relentless tempo and sustain.

    Prime Overload pushes charge gains to 25 per action, soft-capping at a
    higher pool so Ally can enter the stance quickly and stay there longer.
    While Overload is active, Ally gains heavier damage, more swings, and
    self-sustain to offset the usual fragility of the stance.
    """

    plugin_type = "passive"
    id = "ally_overload_prime"
    name = "Prime Overload"
    trigger = "action_taken"
    max_stacks = 300
    stack_display = "number"

    async def apply(self, target: "Stats") -> None:
        """Build charge faster and decay slower when idle."""

        entity_id = id(target)
        if entity_id not in self._overload_charge:
            self._overload_charge[entity_id] = 0
            self._overload_active[entity_id] = False

        if not self._overload_active[entity_id]:
            target.actions_per_turn = 2

        base_charge_gain = 25
        current_charge = self._overload_charge[entity_id]

        if current_charge > 180:
            charge_gain = base_charge_gain * 0.6
        else:
            charge_gain = base_charge_gain

        self._overload_charge[entity_id] += charge_gain

        current_charge = self._overload_charge[entity_id]
        if current_charge >= 100 and not self._overload_active[entity_id]:
            await self._activate_overload(target)

        if not self._overload_active[entity_id]:
            self._overload_charge[entity_id] = max(0, current_charge - 2)

    async def _activate_overload(self, target: "Stats") -> None:
        """Prime Overload stance with heavier hits and lifesteal."""

        entity_id = id(target)
        self._overload_active[entity_id] = True

        target.actions_per_turn = 5

        damage_bonus = StatEffect(
            name=f"{self.id}_damage_bonus",
            stat_modifiers={"atk": int(target.atk * 0.6)},
            duration=-1,
            source=self.id,
        )
        target.add_effect(damage_bonus)

        damage_vulnerability = StatEffect(
            name=f"{self.id}_damage_vulnerability",
            stat_modifiers={"mitigation": -0.2},
            duration=-1,
            source=self.id,
        )
        target.add_effect(damage_vulnerability)

        sustain = StatEffect(
            name=f"{self.id}_sustain",
            stat_modifiers={"regain": max(5, int(target.max_hp * 0.02))},
            duration=-1,
            source=self.id,
        )
        target.add_effect(sustain)

    async def _deactivate_overload(self, target: "Stats") -> None:
        """Tear down Prime Overload effects."""

        entity_id = id(target)
        self._overload_active[entity_id] = False

        effects_to_remove = [
            f"{self.id}_damage_bonus",
            f"{self.id}_damage_vulnerability",
            f"{self.id}_sustain",
        ]
        for effect_name in effects_to_remove:
            target.remove_effect_by_name(effect_name)

        target.actions_per_turn = 2

    async def on_turn_end(self, target: "Stats") -> None:
        """Slower drain while offering a burst of healing each turn."""

        entity_id = id(target)
        if entity_id not in self._overload_charge:
            self._overload_charge[entity_id] = 0
            self._overload_active[entity_id] = False

        if self._overload_active[entity_id]:
            self._overload_charge[entity_id] = max(0, self._overload_charge[entity_id] - 15)

            heal = max(1, int(target.max_hp * 0.04))
            await target.apply_healing(heal, healer=target, source_type="passive", source_name=self.id)

            if self._overload_charge[entity_id] <= 0:
                await self._deactivate_overload(target)

    @classmethod
    def get_description(cls) -> str:
        return (
            "[PRIME] Builds 25 charge per action (reduced past 180) with minimal decay. "
            "At 100 charge, Overload grants five swings per turn, +60% damage, only +20% damage taken, and steady regen. "
            "Drains 15 charge per turn while active and heals 4% max HP each tick."
        )
