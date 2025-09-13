from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import ClassVar
from typing import Iterable

from autofighter.stat_effect import StatEffect

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class LadyFireAndIceDualityEngine:
    """Lady Fire and Ice's Duality Engine passive - elemental flux system."""
    plugin_type = "passive"
    id = "lady_fire_and_ice_duality_engine"
    name = "Duality Engine"
    trigger = "action_taken"  # Triggers when Lady Fire and Ice attacks
    max_stacks = 1  # Only one instance per character
    stack_display = "spinner"

    # Class-level tracking of last element used and flux stacks
    _last_element: ClassVar[dict[int, str]] = {}
    _flux_stacks: ClassVar[dict[int, int]] = {}

    async def apply(
        self,
        owner: "Stats",
        *,
        foes: Iterable["Stats"] | None = None,
        **kwargs,
    ) -> None:
        """Apply Lady Fire and Ice's duality mechanics."""
        entity_id = id(owner)

        # Initialize tracking if not present
        if entity_id not in self._last_element:
            self._last_element[entity_id] = None
            self._flux_stacks[entity_id] = 0

        # Determine current element from the damage type
        current_element = self._determine_current_element(owner)

        # Check if alternating or using same element twice
        if self._last_element[entity_id] is not None:
            if current_element != self._last_element[entity_id]:
                # Alternating elements - gain Elemental Flux stack
                await self._gain_flux_stack(owner)
            else:
                # Same element twice - consume all stacks for effects
                await self._consume_flux_stacks(owner, foes)

        # Update last element used
        self._last_element[entity_id] = current_element

    def _determine_current_element(self, target: "Stats") -> str:
        """Determine the current element from the target's damage type."""
        element = getattr(getattr(target, "damage_type", None), "id", "").lower()
        if "fire" in element:
            return "fire"
        if "ice" in element:
            return "ice"
        return element

    async def _gain_flux_stack(self, target: "Stats") -> None:
        """Gain an Elemental Flux stack."""
        entity_id = id(target)
        self._flux_stacks[entity_id] += 1

        # Apply 5% boost to burn DoT and chill debuff potency per stack
        current_stacks = self._flux_stacks[entity_id]
        potency_bonus = current_stacks * 0.05

        flux_effect = StatEffect(
            name=f"{self.id}_flux_potency",
            stat_modifiers={
                "burn_potency": potency_bonus,
                "chill_potency": potency_bonus,
            },
            duration=-1,  # Permanent until consumed
            source=self.id,
        )
        target.add_effect(flux_effect)

    async def _consume_flux_stacks(
        self,
        target: "Stats",
        foes: Iterable["Stats"] | None = None,
    ) -> None:
        """Consume all flux stacks for beneficial effects."""
        entity_id = id(target)
        stacks_to_consume = self._flux_stacks[entity_id]

        if stacks_to_consume > 0:
            ally_hot_amount = stacks_to_consume * 10  # 10 HP per stack

            ally_hot_effect = StatEffect(
                name=f"{self.id}_flux_ally_hot",
                stat_modifiers={"hp": ally_hot_amount},
                duration=3,  # Three turns of HoT
                source=self.id,
            )
            target.add_effect(ally_hot_effect)

            if foes:
                mitigation_reduction = stacks_to_consume * 0.02
                for foe in foes:
                    debuff = StatEffect(
                        name=f"{self.id}_flux_enemy_mitigation",
                        stat_modifiers={"mitigation": -mitigation_reduction},
                        duration=3,
                        source=self.id,
                    )
                    foe.add_effect(debuff)

            target._active_effects = [
                effect for effect in target._active_effects
                if effect.name != f"{self.id}_flux_potency"
            ]

            self._flux_stacks[entity_id] = 0

    @classmethod
    def get_flux_stacks(cls, target: "Stats") -> int:
        """Get current flux stacks for an entity."""
        return cls._flux_stacks.get(id(target), 0)

    @classmethod
    def get_last_element(cls, target: "Stats") -> str:
        """Get last element used by an entity."""
        return cls._last_element.get(id(target), None)

    @classmethod
    def get_description(cls) -> str:
        return (
            "Alternating fire and ice attacks builds Flux stacks, boosting burn and chill potency by 5% each. "
            "Using the same element twice consumes stacks to heal allies for 10 HP per stack over 3 turns and reduce foe mitigation by 2% per stack."
        )
