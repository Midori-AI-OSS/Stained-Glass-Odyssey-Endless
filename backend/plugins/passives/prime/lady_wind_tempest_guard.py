from dataclasses import dataclass
from typing import TYPE_CHECKING

from autofighter.stat_effect import StatEffect
from plugins.passives.normal.lady_wind_tempest_guard import LadyWindTempestGuard

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class LadyWindTempestGuardPrime(LadyWindTempestGuard):
    """[PRIME] Tempest Guard with thicker gusts and faster refill."""

    plugin_type = "passive"
    id = "lady_wind_tempest_guard_prime"
    name = "Prime Tempest Guard"
    trigger = "turn_start"
    max_stacks = 7
    stack_display = "pips"

    async def on_turn_start(self, target: "Stats", **_: object) -> None:
        entity_id = id(target)
        cls = self.__class__
        existing = cls._gust_stacks.get(entity_id, 0)
        reduced = max(0, existing - 2)

        crit_targets = cls._pending_crits.setdefault(entity_id, set())
        gained = len(crit_targets) * 2
        crit_targets.clear()

        stacks = min(self.max_stacks, reduced + gained)
        cls._gust_stacks[entity_id] = stacks
        if stacks > 0:
            self._apply_turn_gust(target, stacks)

    async def on_damage_taken(
        self,
        target: "Stats",
        _attacker: "Stats",
        damage: int,
        **_: object,
    ) -> None:
        if damage <= 0:
            return
        entity_id = id(target)
        stacks = self._gust_stacks.get(entity_id, 0)
        if stacks <= 0:
            return

        tailwind_heal = max(1, int(damage * 0.08 * stacks))
        try:
            await target.apply_healing(
                tailwind_heal,
                source_type="passive",
                source_name=self.id,
            )
        except Exception:
            pass

        remaining = max(0, stacks - 1)
        self._gust_stacks[entity_id] = remaining
        if remaining > 0:
            self._apply_turn_gust(target, remaining)
        else:
            target.remove_effect_by_name(f"{self.id}_turn_gust")

    def _apply_turn_gust(self, target: "Stats", stacks: int) -> None:
        gust_effect_name = f"{self.id}_turn_gust"
        target.remove_effect_by_name(gust_effect_name)

        dodge_bonus = 0.05 + (stacks * 0.012)
        mitigation_bonus = 0.06 + (stacks * 0.02)
        speed_bonus = stacks * 8
        attack_bonus = max(1, int(target.atk * 0.015 * stacks))

        gust_effect = StatEffect(
            name=gust_effect_name,
            stat_modifiers={
                "dodge_odds": dodge_bonus,
                "mitigation": mitigation_bonus,
                "spd": speed_bonus,
                "atk": attack_bonus,
            },
            duration=1,
            source=self.id,
        )
        target.add_effect(gust_effect)

    @classmethod
    def get_description(cls) -> str:
        return (
            "[PRIME] Crits feed two gust stacks, decay slows, and gusts grant higher dodge, mitigation, speed, and attack. Taking damage returns 8% of it per stack as healing."
        )

