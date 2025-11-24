from dataclasses import dataclass
import random
from typing import TYPE_CHECKING
from weakref import ref

from autofighter.stat_effect import StatEffect
from autofighter.stats import BUS
from plugins.effects.aftertaste import Aftertaste
from plugins.passives.normal.hilander_critical_ferment import HilanderCriticalFerment
from plugins.relics._base import safe_async_task

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class HilanderCriticalFermentPrime(HilanderCriticalFerment):
    """[PRIME] Critical Ferment with denser stacks and bigger aftertaste."""

    plugin_type = "passive"
    id = "hilander_critical_ferment_prime"
    name = "Prime Critical Ferment"
    trigger = "hit_landed"
    stack_display = "pips"

    async def apply(
        self,
        attacker: "Stats",
        hit_target=None,
        damage=None,
        action_type=None,
        event=None,
        stack_index=None,
        **_kwargs,
    ) -> None:
        ferment_stacks = sum(
            1
            for effect in attacker._active_effects
            if effect.name.startswith(f"{self.id}_crit_stack") and effect.name.endswith("_rate")
        )

        if ferment_stacks >= 25:
            chance = max(0.01, 1 - 0.04 * (ferment_stacks - 24))
            if random.random() >= chance:
                return

        stack_id = ferment_stacks + 1
        crit_rate_bonus = StatEffect(
            name=f"{self.id}_crit_stack_{stack_id}_rate",
            stat_modifiers={"crit_rate": 0.08},
            duration=-1,
            source=self.id,
        )
        attacker.add_effect(crit_rate_bonus)

        crit_damage_bonus = StatEffect(
            name=f"{self.id}_crit_stack_{stack_id}_damage",
            stat_modifiers={"crit_damage": 0.16},
            duration=-1,
            source=self.id,
        )
        attacker.add_effect(crit_damage_bonus)

        if getattr(attacker, "_hilander_crit_cb", None) is None:
            attacker_ref = ref(attacker)

            def _crit(crit_attacker, crit_target, crit_damage, *_args, **_kwargs) -> None:
                tgt = attacker_ref()
                if tgt is None:
                    BUS.unsubscribe("critical_hit", _crit)
                    return
                if crit_attacker is tgt:
                    self.on_critical_hit(tgt, crit_target, crit_damage)

            BUS.subscribe("critical_hit", _crit)
            attacker._hilander_crit_cb = _crit

    @classmethod
    def on_critical_hit(cls, attacker: "Stats", target: "Stats", damage: int) -> None:
        ferment_effects = [
            effect
            for effect in attacker._active_effects
            if effect.name.startswith(f"{cls.id}_crit_stack")
        ]
        if not ferment_effects:
            return

        base = int(damage * 0.35)
        if base > 0:
            effect = Aftertaste(base_pot=base)
            safe_async_task(effect.apply(attacker, target))

        highest_stack = 0
        for effect in ferment_effects:
            try:
                parts = effect.name.rsplit("_", 3)
                stack_num = int(parts[2])
                if stack_num > highest_stack:
                    highest_stack = stack_num
            except (IndexError, ValueError):
                continue

        attacker._active_effects = [
            effect
            for effect in attacker._active_effects
            if not (
                effect.name == f"{cls.id}_crit_stack_{highest_stack}_rate"
                or effect.name == f"{cls.id}_crit_stack_{highest_stack}_damage"
            )
        ]

        if cls.get_stacks(attacker) == 0:
            cls._clear_bus_listener(attacker)

    @classmethod
    def get_description(cls) -> str:
        return (
            "[PRIME] Each hit grants +8% crit rate and +16% crit damage. Stacks can reach 25 before slowing. "
            "Critical hits trigger a 35% Aftertaste blast and consume the highest stack."
        )

