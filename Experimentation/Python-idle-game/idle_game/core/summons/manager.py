"""
Summon manager for idle game.
Simplified from backend/autofighter/summons/manager.py.
"""

from __future__ import annotations

from typing import Any

from .base import Summon


class SummonManager:
    """Manages all active summons in combat."""

    def __init__(self):
        """Initialize summon manager."""
        self._summons: dict[str, Summon] = {}
        self._summons_by_summoner: dict[str, list[str]] = {}

    def add_summon(self, summon: Summon) -> None:
        """Add a summon to the manager.
        
        Args:
            summon: Summon instance to add
        """
        # Store summon by instance ID
        self._summons[summon.instance_id] = summon

        # Track by summoner
        if summon.summoner_id not in self._summons_by_summoner:
            self._summons_by_summoner[summon.summoner_id] = []
        self._summons_by_summoner[summon.summoner_id].append(summon.instance_id)

    def remove_summon(self, instance_id: str) -> Summon | None:
        """Remove a summon from the manager.
        
        Args:
            instance_id: Instance ID of summon to remove
            
        Returns:
            Removed summon or None if not found
        """
        summon = self._summons.pop(instance_id, None)

        if summon:
            # Remove from summoner tracking
            if summon.summoner_id in self._summons_by_summoner:
                try:
                    self._summons_by_summoner[summon.summoner_id].remove(instance_id)
                    if not self._summons_by_summoner[summon.summoner_id]:
                        del self._summons_by_summoner[summon.summoner_id]
                except ValueError:
                    pass

        return summon

    def get_summon(self, instance_id: str) -> Summon | None:
        """Get a summon by instance ID.
        
        Args:
            instance_id: Instance ID of summon
            
        Returns:
            Summon or None if not found
        """
        return self._summons.get(instance_id)

    def get_summons_by_summoner(self, summoner_id: str) -> list[Summon]:
        """Get all summons for a specific summoner.
        
        Args:
            summoner_id: ID of summoner
            
        Returns:
            List of summons
        """
        instance_ids = self._summons_by_summoner.get(summoner_id, [])
        return [self._summons[iid] for iid in instance_ids if iid in self._summons]

    def get_all_summons(self) -> list[Summon]:
        """Get all active summons.
        
        Returns:
            List of all summons
        """
        return list(self._summons.values())

    def tick_all_summons(self) -> list[str]:
        """Tick all summons and remove expired ones.
        
        Returns:
            List of instance IDs that were despawned
        """
        despawned: list[str] = []

        for instance_id, summon in list(self._summons.items()):
            # Tick turn counter
            still_active = summon.tick_turn()

            # Check if should despawn
            if not still_active or summon.should_despawn():
                self.remove_summon(instance_id)
                despawned.append(instance_id)

        return despawned

    def clear_summons(self, summoner_id: str | None = None) -> None:
        """Clear all summons or summons for a specific summoner.
        
        Args:
            summoner_id: Optional summoner ID to clear summons for.
                        If None, clears all summons.
        """
        if summoner_id is None:
            # Clear all
            self._summons.clear()
            self._summons_by_summoner.clear()
        else:
            # Clear for specific summoner
            instance_ids = self._summons_by_summoner.get(summoner_id, [])
            for instance_id in instance_ids:
                self._summons.pop(instance_id, None)
            self._summons_by_summoner.pop(summoner_id, None)

    def count_summons(self, summoner_id: str | None = None) -> int:
        """Count summons.
        
        Args:
            summoner_id: Optional summoner ID to count summons for.
                        If None, counts all summons.
            
        Returns:
            Number of summons
        """
        if summoner_id is None:
            return len(self._summons)
        else:
            return len(self._summons_by_summoner.get(summoner_id, []))

    def to_dict(self) -> dict[str, Any]:
        """Convert manager state to dictionary for serialization.
        
        Returns:
            Dictionary representation
        """
        return {
            "summons": [summon.to_dict() for summon in self._summons.values()],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SummonManager:
        """Create manager from dictionary.
        
        Args:
            data: Dictionary with manager state
            
        Returns:
            SummonManager instance
        """
        manager = cls()

        # Restore summons
        for summon_data in data.get("summons", []):
            summon = Summon.from_dict(summon_data)
            manager.add_summon(summon)

        return manager
