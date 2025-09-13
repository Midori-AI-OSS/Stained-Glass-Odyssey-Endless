from dataclasses import dataclass
import random
from typing import TYPE_CHECKING
from typing import ClassVar

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
class KboshiFluxCycle:
    """Kboshi's Flux Cycle passive - random element switching with bonuses."""
    plugin_type = "passive"
    id = "kboshi_flux_cycle"
    name = "Flux Cycle"
    trigger = "turn_start"  # Triggers at start of Kboshi's turn
    stack_display = "pips"

    # Track accumulated damage bonuses and HoT stacks per entity
    _damage_stacks: ClassVar[dict[int, int]] = {}
    _hot_stacks: ClassVar[dict[int, int]] = {}

    # Available damage types for switching
    _damage_types = [Fire, Ice, Wind, Lightning, Light, Dark]

    async def apply(self, target: "Stats") -> None:
        """Apply Flux Cycle element switching mechanics for Kboshi."""
        entity_id = id(target)

        # Initialize tracking if needed
        if entity_id not in self._damage_stacks:
            self._damage_stacks[entity_id] = 0
            self._hot_stacks[entity_id] = 0

        # High chance to switch to random damage type
        if random.random() < 0.8:  # 80% chance to switch
            # Get current damage type
            current_type_id = getattr(target.damage_type, 'id', 'Dark')  # Default to Dark for Kboshi

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
                target._active_effects = [
                    effect
                    for effect in target._active_effects
                    if not effect.name.startswith(f"{self.id}_damage_bonus")
                    and not effect.name.startswith(f"{self.id}_hot_heal")
                ]

                # Reset stacks
                self._damage_stacks[entity_id] = 0
                self._hot_stacks[entity_id] = 0

                # Apply mitigation debuff to foes for one turn
                if stacks > 0:
                    mitigation = stacks * -0.02
                    for foe in getattr(target, "enemies", []):
                        debuff = StatEffect(
                            name=f"{self.id}_mitigation_debuff",
                            stat_modifiers={"mitigation": mitigation},
                            duration=1,
                            source=self.id,
                        )
                        foe.add_effect(debuff)
        else:
            # Element failed to change - gain damage bonus and HoT
            self._damage_stacks[entity_id] += 1
            self._hot_stacks[entity_id] += 1

            # Apply 20% damage bonus per stack
            damage_bonus = StatEffect(
                name=f"{self.id}_damage_bonus_{self._damage_stacks[entity_id]}",
                stat_modifiers={"atk": int(target.atk * 0.2)},
                duration=-1,  # Until element changes
                source=self.id,
            )
            target.add_effect(damage_bonus)

            # Apply small HoT for that turn
            hot_heal = StatEffect(
                name=f"{self.id}_hot_heal_{self._hot_stacks[entity_id]}",
                stat_modifiers={},  # Would need HoT integration
                duration=1,  # One turn
                source=self.id,
            )
            target.add_effect(hot_heal)

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
            "80% chance each turn to switch to a new element. "
            "Failing to switch grants a 20% attack bonus and a small HoT for that turn; "
            "switching clears stacks and applies -2% mitigation to foes per stack."
        )
