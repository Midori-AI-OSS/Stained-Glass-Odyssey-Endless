from dataclasses import dataclass
import random
from typing import TYPE_CHECKING
from typing import Optional
from weakref import ref

from autofighter.stat_effect import StatEffect
from autofighter.stats import BUS
from plugins.effects.aftertaste import Aftertaste
from plugins.relics._base import safe_async_task

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class HilanderCriticalFerment:
    """Hilander's Critical Ferment passive - builds crit rate/damage, consumes on crit."""
    plugin_type = "passive"
    id = "hilander_critical_ferment"
    name = "Critical Ferment"
    trigger = "hit_landed"  # Triggers when Hilander lands a hit
    stack_display = "pips"  # Unlimited stacks with numeric fallback past five
    async def apply(
        self,
        attacker: "Stats",
        hit_target: Optional["Stats"] = None,
        damage: Optional[int] = None,
        action_type: Optional[str] = None,
        event: Optional[str] = None,
        stack_index: Optional[int] = None,
        **_kwargs,
    ) -> None:
        """Apply crit building mechanics for Hilander."""
        # Build 5% crit rate and 10% crit damage each hit

        # Count existing ferment stacks
        ferment_stacks = sum(
            1
            for effect in attacker._active_effects
            if effect.name.startswith(f"{self.id}_crit_stack") and effect.name.endswith("_rate")
        )

        if ferment_stacks >= 20:
            chance = max(0.01, 1 - 0.05 * (ferment_stacks - 19))
            if random.random() >= chance:
                return

        # Add a new stack
        stack_id = ferment_stacks + 1
        crit_rate_bonus = StatEffect(
            name=f"{self.id}_crit_stack_{stack_id}_rate",
            stat_modifiers={"crit_rate": 0.05},  # +5% crit rate
            duration=-1,  # Permanent until consumed
            source=self.id,
        )
        attacker.add_effect(crit_rate_bonus)

        crit_damage_bonus = StatEffect(
            name=f"{self.id}_crit_stack_{stack_id}_damage",
            stat_modifiers={"crit_damage": 0.1},  # +10% crit damage
            duration=-1,  # Permanent until consumed
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
        return None

    @classmethod
    def on_critical_hit(cls, attacker: "Stats", target: "Stats", damage: int) -> None:
        """Handle critical hit - unleash Aftertaste and consume one stack."""
        ferment_effects = [
            effect
            for effect in attacker._active_effects
            if effect.name.startswith(f"{cls.id}_crit_stack")
        ]
        if not ferment_effects:
            return

        base = int(damage * 0.25)
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
    def get_stacks(cls, target: "Stats") -> int:
        """Return current ferment stacks for Hilander."""
        return sum(
            1
            for effect in getattr(target, "_active_effects", [])
            if effect.name.startswith(f"{cls.id}_crit_stack_") and effect.name.endswith("_rate")
        )

    @staticmethod
    def _clear_bus_listener(target: "Stats") -> None:
        """Remove the critical hit callback if it was registered."""
        callback = getattr(target, "_hilander_crit_cb", None)
        if callback is not None:
            BUS.unsubscribe("critical_hit", callback)
        if hasattr(target, "_hilander_crit_cb"):
            delattr(target, "_hilander_crit_cb")

    async def on_defeat(self, owner: "Stats") -> None:
        """Clean up any lingering bus listener when Hilander is defeated."""
        self._clear_bus_listener(owner)

    @classmethod
    def get_description(cls) -> str:
        return (
            "Each hit grants +5% crit rate and +10% crit damage. "
            "Beyond 20 stacks, stack gain odds drop 5% per extra stack (min 1%). "
            "A critical hit triggers Aftertaste and consumes one stack."
        )
