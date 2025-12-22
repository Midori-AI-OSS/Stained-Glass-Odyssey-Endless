from dataclasses import dataclass
import random
from typing import TYPE_CHECKING, ClassVar

from autofighter.effects import HealingOverTime
from autofighter.stat_effect import StatEffect
from plugins.damage_types.dark import Dark
from plugins.damage_types.fire import Fire
from plugins.damage_types.ice import Ice
from plugins.damage_types.light import Light
from plugins.damage_types.lightning import Lightning
from plugins.damage_types.wind import Wind

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class KboshiFluxCycleGlitched:
    """[GLITCHED] Kboshi's Flux Cycle - element switching with doubled bonuses.

    This glitched variant doubles the damage bonus (40% per stack instead of 20%)
    and HoT healing (10% max HP per stack instead of 5%), while maintaining
    the same 80% element switch chance. The mitigation debuff on switch is
    also doubled (-4% per stack instead of -2%).
    """
    plugin_type = "passive"
    id = "kboshi_flux_cycle_glitched"
    name = "Glitched Flux Cycle"
    trigger = "turn_start"
    stack_display = "pips"

    # Track accumulated damage bonuses and HoT stacks per entity
    _damage_stacks: ClassVar[dict[int, int]] = {}
    _hot_stacks: ClassVar[dict[int, int]] = {}

    # Available damage types for switching
    _damage_types = [Fire, Ice, Wind, Lightning, Light, Dark]

    async def apply(self, target: "Stats") -> None:
        """Apply Flux Cycle element switching mechanics with doubled bonuses."""
        entity_id = id(target)

        # Initialize tracking if needed
        if entity_id not in self._damage_stacks:
            self._damage_stacks[entity_id] = 0
            self._hot_stacks[entity_id] = 0

        # High chance to switch to random damage type
        if random.random() < 0.8:  # 80% chance to switch
            # Get current damage type
            current_type_id = getattr(target.damage_type, 'id', 'Dark')

            # Filter out current type to ensure we actually switch
            available_types = [dt for dt in self._damage_types
                             if dt().id != current_type_id]

            # If no different types available (shouldn't happen), use all types
            if not available_types:
                available_types = self._damage_types

            # Select random new damage type
            new_damage_type_class = random.choice(available_types)
            new_damage_type = new_damage_type_class()

            # Actually switch the damage type
            target.damage_type = new_damage_type

            # Element successfully changed - remove accumulated stacks
            if self._damage_stacks[entity_id] > 0 or self._hot_stacks[entity_id] > 0:
                stacks = self._damage_stacks[entity_id]

                # Remove existing bonus effects
                target.remove_effect_by_source(self.id)

                # Clear any active HoTs from flux cycle
                if hasattr(target, "effect_manager") and target.effect_manager:
                    await target.effect_manager.remove_hots(
                        lambda hot: hot.id.startswith(f"{self.id}_hot_{entity_id}")
                    )

                # Reset stacks
                self._damage_stacks[entity_id] = 0
                self._hot_stacks[entity_id] = 0

                # Apply DOUBLED mitigation debuff to foes for one turn (-4% per stack)
                if stacks > 0:
                    mitigation = stacks * -0.04  # Doubled from -0.02
                    for foe in getattr(target, "enemies", []):
                        debuff = StatEffect(
                            name=f"{self.id}_mitigation_debuff",
                            stat_modifiers={"mitigation": mitigation},
                            duration=1,
                            source=self.id,
                        )
                        foe.add_effect(debuff)
        else:
            # Element failed to change - gain DOUBLED damage bonus and HoT
            self._damage_stacks[entity_id] += 1
            self._hot_stacks[entity_id] += 1

            # Apply DOUBLED 40% damage bonus per stack (was 20%)
            base_attack = (
                int(target.get_base_stat("atk"))
                if hasattr(target, "get_base_stat")
                else int(getattr(target, "_base_atk", target.atk))
            )
            bonus_amount = max(1, int(base_attack * 0.4))  # Doubled from 0.2
            damage_bonus = StatEffect(
                name=f"{self.id}_damage_bonus_{self._damage_stacks[entity_id]}",
                stat_modifiers={"atk": bonus_amount},
                duration=-1,  # Until element changes
                source=self.id,
            )
            target.add_effect(damage_bonus)

            # Apply DOUBLED HoT - heal 10% max HP per stack (was 5%)
            heal_amount = max(1, int(target.max_hp * 0.10 * self._hot_stacks[entity_id]))
            hot = HealingOverTime(
                name=f"Glitched Flux Cycle HoT (Stack {self._hot_stacks[entity_id]})",
                healing=heal_amount,
                turns=1,
                id=f"{self.id}_hot_{entity_id}_{self._hot_stacks[entity_id]}",
                source=target,
            )
            # Add HoT through effect manager if available
            mgr = getattr(target, "effect_manager", None)
            if mgr is None:
                from autofighter.effects import EffectManager

                mgr = EffectManager(target)
                target.effect_manager = mgr

            await mgr.add_hot(hot)

    @classmethod
    def get_damage_stacks(cls, target: "Stats") -> int:
        """Get current damage bonus stacks."""
        return cls._damage_stacks.get(id(target), 0)

    @classmethod
    def get_hot_stacks(cls, target: "Stats") -> int:
        """Get current HoT stacks."""
        return cls._hot_stacks.get(id(target), 0)

    @classmethod
    def get_stacks(cls, target: "Stats") -> int:
        """Return current damage bonus stacks."""
        return cls.get_damage_stacks(target)

    @classmethod
    def get_description(cls) -> str:
        return (
            "[GLITCHED] 80% chance each turn to switch to a new element. "
            "Failing to switch grants a 40% attack bonus (doubled) and a 10% max HP HoT (doubled) for that turn; "
            "switching clears stacks and applies -4% mitigation (doubled) to foes per stack."
        )
