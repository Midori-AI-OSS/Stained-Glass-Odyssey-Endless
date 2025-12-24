"""Relic manager for equipped relic tracking and management.

Manages a character's relic collection and handles applying/removing
relic effects with proper stack counting.
"""

from collections import Counter
import logging
from typing import Dict
from typing import List

from .effect_manager import EffectManager
from .relics import Relic
from .relics import instantiate_relic
from .stats import Stats

log = logging.getLogger(__name__)


class RelicManager:
    """Manages relic collection and effect application for a character."""

    def __init__(self, stats: Stats, effect_manager: EffectManager):
        """Initialize relic manager.

        Args:
            stats: Character stats
            effect_manager: Effect manager for applying relic effects
        """
        self.stats = stats
        self.effect_manager = effect_manager

        # Equipped relics (list of relic IDs, allows duplicates for stacking)
        self.equipped: List[str] = []

        # Cache for applied relic instances (for removal)
        self._applied_relics: Dict[str, Relic] = {}

    def add_relic(self, relic_id: str) -> bool:
        """Add a relic to equipped list.

        Relics can stack - adding the same relic multiple times
        increases its power.

        Args:
            relic_id: Relic ID to add

        Returns:
            True if added successfully
        """
        # Verify relic exists
        relic = instantiate_relic(relic_id)
        if relic is None:
            log.error("Cannot add unknown relic: %s", relic_id)
            return False

        self.equipped.append(relic_id)
        log.info("Added relic: %s (total stacks: %d)", relic_id, self.equipped.count(relic_id))

        # Reapply all relics to update stacks
        self.reapply_all()
        return True

    def remove_relic(self, relic_id: str, remove_all: bool = False) -> bool:
        """Remove a relic from equipped list.

        Args:
            relic_id: Relic ID to remove
            remove_all: If True, remove all stacks; if False, remove one

        Returns:
            True if removed, False if not equipped
        """
        if relic_id not in self.equipped:
            log.warning("Relic %s not equipped", relic_id)
            return False

        if remove_all:
            # Remove all stacks
            count = self.equipped.count(relic_id)
            self.equipped = [rid for rid in self.equipped if rid != relic_id]
            log.info("Removed all %d stacks of relic: %s", count, relic_id)
        else:
            # Remove one stack
            self.equipped.remove(relic_id)
            log.info("Removed relic: %s (remaining stacks: %d)", relic_id, self.equipped.count(relic_id))

        # Reapply all relics to update stacks
        self.reapply_all()
        return True

    def get_stack_count(self, relic_id: str) -> int:
        """Get number of stacks for a relic.

        Args:
            relic_id: Relic ID to check

        Returns:
            Number of stacks (0 if not equipped)
        """
        return self.equipped.count(relic_id)

    def get_unique_relics(self) -> List[str]:
        """Get list of unique equipped relic IDs.

        Returns:
            List of unique relic IDs
        """
        return list(set(self.equipped))

    def get_relic_counts(self) -> Dict[str, int]:
        """Get stack counts for all equipped relics.

        Returns:
            Dict mapping relic ID to stack count
        """
        return dict(Counter(self.equipped))

    def apply_relic(self, relic_id: str) -> bool:
        """Apply or update a single relic's effects.

        Automatically handles stack counting.

        Args:
            relic_id: Relic ID to apply

        Returns:
            True if applied successfully
        """
        # Get stack count
        stacks = self.get_stack_count(relic_id)
        if stacks == 0:
            log.warning("Cannot apply relic %s - not equipped", relic_id)
            return False

        # Instantiate relic
        relic = instantiate_relic(relic_id)
        if relic is None:
            log.error("Failed to instantiate relic: %s", relic_id)
            return False

        try:
            # Remove old effects if previously applied
            if relic_id in self._applied_relics:
                old_relic = self._applied_relics[relic_id]
                old_relic.remove(self.effect_manager)

            # Apply with current stack count
            relic.apply(self.stats, self.effect_manager, stacks)

            # Cache for later removal
            self._applied_relics[relic_id] = relic

            log.info("Applied relic %s with %d stacks", relic_id, stacks)
            return True

        except Exception as e:
            log.error("Error applying relic %s: %s", relic_id, e)
            return False

    def remove_relic_effects(self, relic_id: str) -> bool:
        """Remove a relic's effects without unequipping it.

        Args:
            relic_id: Relic ID to remove effects for

        Returns:
            True if removed successfully
        """
        if relic_id not in self._applied_relics:
            log.debug("Relic %s effects not currently applied", relic_id)
            return False

        try:
            relic = self._applied_relics[relic_id]
            relic.remove(self.effect_manager)
            del self._applied_relics[relic_id]

            log.info("Removed effects for relic: %s", relic_id)
            return True

        except Exception as e:
            log.error("Error removing relic %s effects: %s", relic_id, e)
            return False

    def reapply_all(self) -> None:
        """Reapply all equipped relics.

        Used when stack counts change or effects need refreshing.
        """
        # Get unique relics
        unique_relics = self.get_unique_relics()

        # Remove all effects first
        for relic_id in list(self._applied_relics.keys()):
            self.remove_relic_effects(relic_id)

        # Reapply each unique relic with current stacks
        for relic_id in unique_relics:
            self.apply_relic(relic_id)

        log.info("Reapplied %d unique relics", len(unique_relics))

    def get_relic_instances(self) -> List[tuple[Relic, int]]:
        """Get relic instances with their stack counts.

        Returns:
            List of (relic_instance, stack_count) tuples
        """
        result = []
        for relic_id, stacks in self.get_relic_counts().items():
            relic = instantiate_relic(relic_id)
            if relic:
                result.append((relic, stacks))
        return result

    def has_relic(self, relic_id: str) -> bool:
        """Check if a relic is equipped.

        Args:
            relic_id: Relic ID to check

        Returns:
            True if equipped
        """
        return relic_id in self.equipped

    def clear(self) -> None:
        """Remove all relics and their effects."""
        # Remove all effects
        for relic_id in list(self._applied_relics.keys()):
            self.remove_relic_effects(relic_id)

        # Clear equipped list
        self.equipped.clear()
        log.info("Cleared all relics")

    def get_total_relic_count(self) -> int:
        """Get total number of equipped relics (including stacks).

        Returns:
            Total relic count
        """
        return len(self.equipped)

    def get_unique_relic_count(self) -> int:
        """Get number of unique relics equipped.

        Returns:
            Unique relic count
        """
        return len(set(self.equipped))
