"""Relic system for the idle game.

This module provides the Relic base class and relic registry for managing
special items that grant passive bonuses. Ported from backend with adaptations
for tick-based Qt system (no async/await).
"""

from dataclasses import dataclass
from dataclasses import field
import logging
import random
from typing import Dict
from typing import List
from typing import Optional

from .effect_manager import EffectManager
from .effects import StatModifier
from .stats import Stats

log = logging.getLogger(__name__)


@dataclass
class Relic:
    """Base relic class representing a special item with passive effects.

    Relics can stack - having multiple copies increases their power.
    Each relic has a star rating indicating rarity.
    """

    id: str = ""
    name: str = ""
    stars: int = 1
    effects: Dict[str, float] = field(default_factory=dict)
    full_about: str = "Relic description missing"
    summarized_about: str = "Relic summary missing"

    def apply(
        self,
        stats: Stats,
        effect_manager: EffectManager,
        stacks: int = 1
    ) -> None:
        """Apply relic effects to a character's stats.

        Creates permanent stat modifiers based on the relic's effects dict.
        Effects scale multiplicatively with stacks - each stack multiplies
        the bonus (e.g., 2 stacks of +50% = 2.25x total, not 2x).

        Args:
            stats: Character stats to apply effects to
            effect_manager: Effect manager for the character
            stacks: Number of this relic owned (for stacking)
        """
        if not self.effects:
            log.debug("Relic %s has no effects to apply", self.id)
            return

        if stacks < 1:
            log.warning("Invalid stack count %d for relic %s", stacks, self.id)
            return

        log.info("Applying relic %s (x%d) to character", self.id, stacks)

        # Apply stack multiplier to effects
        # Formula: (1 + effect)^stacks
        # Example: 50% bonus with 2 stacks = (1.5)^2 = 2.25x total
        multipliers = {}
        for stat_name, multiplier in self.effects.items():
            # Calculate stacked multiplier
            stacked_mult = (1 + multiplier) ** stacks
            multipliers[stat_name] = stacked_mult

            log.debug(
                "Relic %s: %s x%d = %.2fx (base %.1f%%)",
                self.id,
                stat_name,
                stacks,
                stacked_mult,
                multiplier * 100
            )

        if multipliers:
            modifier = StatModifier(
                id=f"{self.id}_relic",
                name=f"{self.name} (x{stacks})",
                stats=stats,
                multipliers=multipliers,
                turns=-1,  # Permanent
                bypass_diminishing=False
            )

            effect_manager.add_modifier(modifier)

    def remove(self, effect_manager: EffectManager) -> None:
        """Remove relic effects from a character.

        Args:
            effect_manager: Effect manager to remove from
        """
        # Find and remove modifiers by ID (relic_id + "_relic")
        modifier_id = f"{self.id}_relic"
        to_remove = [mod for mod in effect_manager.mods if mod.id == modifier_id]
        for mod in to_remove:
            mod.remove()
            if mod in effect_manager.mods:
                effect_manager.mods.remove(mod)

        log.debug("Removed relic %s effects", self.id)

    def get_about_str(self, stacks: int = 1, concise: bool = False) -> str:
        """Get the relic description.

        Args:
            stacks: Number of stacks for description
            concise: If True, return summarized version

        Returns:
            Relic description string
        """
        return self.summarized_about if concise else self.full_about_stacks(stacks)

    def full_about_stacks(self, stacks: int) -> str:
        """Get full description with stack information.

        Override in subclasses to provide stack-specific descriptions.

        Args:
            stacks: Number of stacks

        Returns:
            Stack-specific description
        """
        return self.full_about


class RelicRegistry:
    """Registry for managing available relics.

    Provides relic lookup, random selection, and instantiation.
    """

    def __init__(self):
        self._relics: Dict[str, type[Relic]] = {}

    def register(self, relic_cls: type[Relic]) -> None:
        """Register a relic class.

        Args:
            relic_cls: Relic class to register
        """
        # Create instance to get ID
        instance = relic_cls()
        if not instance.id:
            log.warning("Relic class %s has no ID, skipping registration", relic_cls.__name__)
            return

        self._relics[instance.id] = relic_cls
        log.debug("Registered relic: %s", instance.id)

    def get(self, relic_id: str) -> Optional[type[Relic]]:
        """Get relic class by ID.

        Args:
            relic_id: Relic ID to look up

        Returns:
            Relic class or None if not found
        """
        return self._relics.get(relic_id)

    def instantiate(self, relic_id: str) -> Optional[Relic]:
        """Create a relic instance.

        Args:
            relic_id: Relic ID to instantiate

        Returns:
            Relic instance or None if not found
        """
        relic_cls = self.get(relic_id)
        if relic_cls is None:
            log.warning("Relic not found: %s", relic_id)
            return None
        return relic_cls()

    def get_by_stars(self, stars: int) -> List[type[Relic]]:
        """Get all relics with the given star rating.

        Args:
            stars: Star rating to filter by

        Returns:
            List of relic classes
        """
        result = []
        for relic_cls in self._relics.values():
            instance = relic_cls()
            if instance.stars == stars:
                result.append(relic_cls)
        return result

    def get_random_relics(
        self,
        stars: int,
        count: int = 3,
        exclude: Optional[List[str]] = None
    ) -> List[Relic]:
        """Get random relics for selection.

        Note: Unlike cards, relics can be offered even if already owned
        (stacking is allowed). The exclude list is still supported for
        special cases.

        Args:
            stars: Star rating to select from
            count: Number of relics to return
            exclude: List of relic IDs to exclude (optional)

        Returns:
            List of relic instances
        """
        exclude = exclude or []
        available = [
            relic_cls for relic_cls in self.get_by_stars(stars)
            if relic_cls().id not in exclude
        ]

        if not available:
            log.debug("No relics available for stars=%d", stars)
            return []

        # Sample up to count relics
        k = min(count, len(available))
        selected = random.sample(available, k)
        return [cls() for cls in selected]

    def get_all_ids(self) -> List[str]:
        """Get all registered relic IDs.

        Returns:
            List of relic IDs
        """
        return list(self._relics.keys())


# Global relic registry
_RELIC_REGISTRY = RelicRegistry()


def register_relic(relic_cls: type[Relic]) -> type[Relic]:
    """Decorator to register a relic class.

    Usage:
        @register_relic
        class MyRelic(Relic):
            ...

    Args:
        relic_cls: Relic class to register

    Returns:
        The relic class (unchanged)
    """
    _RELIC_REGISTRY.register(relic_cls)
    return relic_cls


def get_relic_registry() -> RelicRegistry:
    """Get the global relic registry.

    Returns:
        Global relic registry instance
    """
    return _RELIC_REGISTRY


def instantiate_relic(relic_id: str) -> Optional[Relic]:
    """Create a relic instance by ID.

    Args:
        relic_id: Relic ID to instantiate

    Returns:
        Relic instance or None if not found
    """
    return _RELIC_REGISTRY.instantiate(relic_id)


def get_random_relics(
    stars: int,
    count: int = 3,
    exclude: Optional[List[str]] = None
) -> List[Relic]:
    """Get random relics for selection.

    Args:
        stars: Star rating to select from
        count: Number of relics to return
        exclude: List of relic IDs to exclude

    Returns:
        List of relic instances
    """
    return _RELIC_REGISTRY.get_random_relics(stars, count, exclude)
