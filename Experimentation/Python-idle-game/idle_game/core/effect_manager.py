"""Effect manager for tracking and processing status effects.

Manages DoT, HoT, stat modifiers, and passive abilities for a Stats object.
"""

from collections import Counter
import logging
from typing import Any
from typing import Callable
from typing import List
from typing import Optional

from .effects import DamageOverTime
from .effects import HealingOverTime
from .effects import StatModifier
from .stats import Stats

log = logging.getLogger(__name__)


class EffectManager:
    """Manage DoT, HoT, and stat modifier effects on a Stats object."""

    def __init__(self, stats: Stats, debug: bool = False) -> None:
        """Initialize the effect manager.

        Args:
            stats: Stats object to manage effects for
            debug: Enable debug logging
        """
        self.stats = stats
        self.dots: List[DamageOverTime] = []
        self.hots: List[HealingOverTime] = []
        self.mods: List[StatModifier] = []
        self._debug = debug

    def add_dot(
        self,
        effect: DamageOverTime,
        max_stacks: Optional[int] = None
    ) -> None:
        """Attach a DoT instance to the tracked stats.

        DoTs with the same id stack independently. When max_stacks is provided,
        extra applications beyond that limit are ignored.

        Args:
            effect: DamageOverTime effect to add
            max_stacks: Maximum number of stacks allowed
        """
        if self.stats.hp <= 0:
            return

        if max_stacks is not None:
            current = len([d for d in self.dots if d.id == effect.id])
            if current >= max_stacks:
                return

        self.dots.append(effect)
        if hasattr(self.stats, 'dots'):
            self.stats.dots.append(effect.id)

    def add_hot(self, effect: HealingOverTime) -> None:
        """Attach a HoT instance to the tracked stats.

        Healing effects accumulate; each copy heals separately every tick.

        Args:
            effect: HealingOverTime effect to add
        """
        if self.stats.hp <= 0:
            return

        self.hots.append(effect)
        if hasattr(self.stats, 'hots'):
            self.stats.hots.append(effect.id)

    def remove_hots(self, predicate: Callable[[HealingOverTime], bool]) -> int:
        """Remove HoT instances matching predicate.

        Args:
            predicate: Function that returns True for HoTs to remove

        Returns:
            Number of removed effects
        """
        matching = [hot for hot in list(self.hots) if predicate(hot)]
        if not matching:
            return 0

        for hot in matching:
            if hot in self.hots:
                self.hots.remove(hot)

            if hasattr(self.stats, "hots"):
                while hot.id in self.stats.hots:
                    self.stats.hots.remove(hot.id)

        return len(matching)

    def add_modifier(self, effect: StatModifier) -> None:
        """Attach a stat modifier to the tracked stats.

        Removes any existing modifiers with the same ID before adding.

        Args:
            effect: StatModifier to add
        """
        # Remove exact same instance if present
        if any(existing is effect for existing in self.mods):
            self.mods[:] = [mod for mod in self.mods if mod is not effect]

        # Remove duplicates by ID
        duplicates = [existing for existing in self.mods if existing.id == effect.id]
        duplicates_removed = False

        for existing in duplicates:
            existing.remove()
            duplicates_removed = True

        if duplicates:
            self.mods[:] = [mod for mod in self.mods if mod not in duplicates]

        if duplicates_removed:
            effect._effect_applied = False

        if not effect._effect_applied:
            effect.apply()

        if hasattr(self.stats, 'mods'):
            while effect.id in self.stats.mods:
                self.stats.mods.remove(effect.id)

        self.mods.append(effect)
        if hasattr(self.stats, 'mods'):
            self.stats.mods.append(effect.id)

    def tick_dots(self) -> int:
        """Process all DoT effects for one tick.

        Returns:
            Number of expired DoT effects
        """
        if self.stats.hp <= 0:
            return 0

        expired_count = 0
        remaining_dots = []

        for dot in list(self.dots):
            if self._debug:
                log.debug(f"{self.stats.id if hasattr(self.stats, 'id') else 'entity'} {dot.name} tick")

            still_active = dot.tick(self.stats)

            if still_active:
                remaining_dots.append(dot)
            else:
                expired_count += 1
                if hasattr(self.stats, "dots"):
                    while dot.id in self.stats.dots:
                        self.stats.dots.remove(dot.id)

            # Early termination if character dies
            if self.stats.hp <= 0:
                break

        self.dots = remaining_dots
        return expired_count

    def tick_hots(self) -> int:
        """Process all HoT effects for one tick.

        Returns:
            Number of expired HoT effects
        """
        if self.stats.hp <= 0:
            return 0

        expired_count = 0
        remaining_hots = []

        for hot in list(self.hots):
            if self._debug:
                log.debug(f"{self.stats.id if hasattr(self.stats, 'id') else 'entity'} {hot.name} tick")

            still_active = hot.tick(self.stats)

            if still_active:
                remaining_hots.append(hot)
            else:
                expired_count += 1
                if hasattr(self.stats, "hots"):
                    while hot.id in self.stats.hots:
                        self.stats.hots.remove(hot.id)

        self.hots = remaining_hots
        return expired_count

    def tick_modifiers(self) -> int:
        """Process all stat modifier effects for one tick.

        Returns:
            Number of expired modifier effects
        """
        expired_count = 0
        remaining_mods = []

        for mod in list(self.mods):
            if self._debug:
                log.debug(f"{self.stats.id if hasattr(self.stats, 'id') else 'entity'} {mod.name} tick")

            still_active = mod.tick()

            if still_active:
                remaining_mods.append(mod)
            else:
                expired_count += 1
                if hasattr(self.stats, "mods"):
                    while mod.id in self.stats.mods:
                        self.stats.mods.remove(mod.id)

        self.mods = remaining_mods
        return expired_count

    def tick_all(self, order: str = "dots_hots_mods") -> dict[str, int]:
        """Process all effects for one tick in specified order.

        Args:
            order: Processing order, one of:
                - "dots_hots_mods" (default)
                - "hots_dots_mods"
                - "mods_dots_hots"

        Returns:
            Dict with counts of expired effects by type
        """
        results = {
            "dots_expired": 0,
            "hots_expired": 0,
            "mods_expired": 0,
        }

        if order == "dots_hots_mods":
            results["dots_expired"] = self.tick_dots()
            if self.stats.hp > 0:
                results["hots_expired"] = self.tick_hots()
            results["mods_expired"] = self.tick_modifiers()
        elif order == "hots_dots_mods":
            results["hots_expired"] = self.tick_hots()
            if self.stats.hp > 0:
                results["dots_expired"] = self.tick_dots()
            results["mods_expired"] = self.tick_modifiers()
        elif order == "mods_dots_hots":
            results["mods_expired"] = self.tick_modifiers()
            if self.stats.hp > 0:
                results["dots_expired"] = self.tick_dots()
                results["hots_expired"] = self.tick_hots()
        else:
            log.warning(f"Unknown tick order '{order}', using default")
            return self.tick_all(order="dots_hots_mods")

        return results

    def tick_passives(
        self,
        order: str = "player_first",
        passive_registry: Optional[Any] = None,
        others: Optional[List[Any]] = None
    ) -> None:
        """Trigger passive abilities at end of turn.

        Args:
            order: Processing order hint (for future use)
            passive_registry: PassiveRegistry to use for triggering
            others: List of other entities (for on_death effects)
        """
        if not hasattr(self.stats, "passives"):
            return

        if passive_registry is None:
            return

        # Get passives that should tick
        counts = Counter(self.stats.passives)
        tick_passives = []

        for pid, count in counts.items():
            cls = passive_registry.get_passive(pid)
            if cls is None:
                continue

            # Check if passive has turn end handling
            if hasattr(cls, 'on_turn_end') or hasattr(cls, 'tick') or getattr(cls, 'trigger', None) == 'turn_end':
                stacks = min(count, getattr(cls, 'max_stacks', count))
                for _ in range(stacks):
                    tick_passives.append((pid, cls))

        if not tick_passives:
            return

        if self._debug:
            log.debug(f"{self.stats.id if hasattr(self.stats, 'id') else 'entity'} processing {len(tick_passives)} passive abilities")

        # Process passives
        for pid, cls in tick_passives:
            if self._debug:
                log.debug(f"{self.stats.id if hasattr(self.stats, 'id') else 'entity'} {pid} passive tick")

            passive_instance = cls()

            # Try turn end processing first
            if hasattr(passive_instance, 'on_turn_end'):
                passive_instance.on_turn_end(self.stats)
            # Fall back to tick method if available
            elif hasattr(passive_instance, 'tick'):
                passive_instance.tick(self.stats)
            # Fall back to general apply for turn_end triggers
            elif getattr(cls, 'trigger', None) == 'turn_end':
                try:
                    passive_instance.apply(self.stats)
                except TypeError:
                    pass

            # Early termination if character dies
            if self.stats.hp <= 0:
                break

        # Handle on_death effects if character died
        if self.stats.hp <= 0 and others is not None:
            for eff in list(self.dots):
                on_death = getattr(eff, "on_death", None)
                if callable(on_death):
                    on_death(others)

    def on_action(self) -> bool:
        """Run any per-action hooks on attached effects.

        Returns:
            False if any effect cancels the action, True otherwise
        """
        for eff in list(self.dots) + list(self.hots):
            handler = getattr(eff, "on_action", None)
            if callable(handler):
                if self._debug:
                    log.debug(f"{self.stats.id if hasattr(self.stats, 'id') else 'entity'} {eff.name} action")

                result = handler(self.stats)
                if result is False:
                    return False

        return True

    def cleanup(self, target: Optional[Stats] = None) -> None:
        """Clear remaining effects and detach status names from the stats.

        Battle resolution calls this to ensure effects don't leak across battles.

        Args:
            target: Optional target stats (unused, for API compatibility)
        """
        try:
            for mod in list(self.mods):
                try:
                    mod.remove()
                except Exception:
                    pass
        finally:
            self.dots.clear()
            self.hots.clear()
            self.mods.clear()

            try:
                if hasattr(self.stats, 'dots'):
                    self.stats.dots = []
                if hasattr(self.stats, 'hots'):
                    self.stats.hots = []
                if hasattr(self.stats, 'mods'):
                    self.stats.mods = []
            except Exception:
                pass
