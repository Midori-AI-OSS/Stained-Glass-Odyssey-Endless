from __future__ import annotations

from collections import Counter
import logging
from pathlib import Path
from typing import Any
from typing import Optional

from plugins import PluginLoader

log = logging.getLogger(__name__)

PASSIVE_LOADER: PluginLoader | None = None
PASSIVE_REGISTRY: dict[str, type] | None = None


def discover() -> dict[str, type]:
    """Load passive plugins once and return the registry."""
    global PASSIVE_LOADER
    global PASSIVE_REGISTRY

    if PASSIVE_REGISTRY is None:
        plugin_dir = Path(__file__).resolve().parents[1] / "plugins" / "passives"
        PASSIVE_LOADER = PluginLoader(required=["passive"])
        PASSIVE_LOADER.discover(str(plugin_dir))
        PASSIVE_REGISTRY = PASSIVE_LOADER.get_plugins("passive")
    assert PASSIVE_REGISTRY is not None
    return PASSIVE_REGISTRY


class PassiveRegistry:
    def __init__(self) -> None:
        self._registry = discover()

    async def trigger(self, event: str, owner, **kwargs) -> None:
        """Trigger passives for a given event with optional context.

        Notes:
            The second parameter was renamed from `target` to `owner` to avoid
            collisions with a `target=` keyword argument commonly passed in
            `**kwargs` (e.g., the target of an action). This prevents the
            "multiple values for argument 'target'" error.
        """
        counts = Counter(owner.passives)
        for pid, count in counts.items():
            cls = self._registry.get(pid)
            if cls is None or getattr(cls, "trigger", None) != event:
                continue
            stacks = min(count, getattr(cls, "max_stacks", count))
            for stack_idx in range(stacks):
                passive_instance = cls()
                # Try to call apply with context, fall back to simple apply for compatibility
                try:
                    await passive_instance.apply(owner, stack_index=stack_idx, **kwargs)
                except TypeError:
                    # Fall back to simple apply for existing passives that don't accept kwargs
                    await passive_instance.apply(owner)

                # If this passive provides an event-specific handler, call it too.
                # This enables richer behaviors (e.g., on_action_taken) while
                # preserving backward compatibility with apply-only passives.
                if event == "action_taken" and hasattr(
                    passive_instance, "on_action_taken"
                ):
                    try:
                        await passive_instance.on_action_taken(owner, **kwargs)
                    except TypeError:
                        await passive_instance.on_action_taken(owner)

    async def trigger_damage_taken(
        self, target, attacker: Optional[Any] = None, damage: int = 0
    ) -> None:
        """Trigger passives specifically for damage taken events."""
        counts = Counter(target.passives)
        for pid, count in counts.items():
            cls = self._registry.get(pid)
            if cls is None:
                continue

            passive_instance = cls()

            # Check if passive has on_damage_taken method (regardless of trigger type)
            if hasattr(passive_instance, "on_damage_taken"):
                stacks = min(count, getattr(cls, "max_stacks", count))
                for _ in range(stacks):
                    await passive_instance.on_damage_taken(target, attacker, damage)

            # Also trigger passives with explicit damage_taken trigger
            if getattr(cls, "trigger", None) == "damage_taken":
                stacks = min(count, getattr(cls, "max_stacks", count))
                for _ in range(stacks):
                    try:
                        await passive_instance.apply(
                            target, attacker=attacker, damage=damage
                        )
                    except TypeError:
                        await passive_instance.apply(target)

    async def trigger_turn_end(self, target) -> None:
        """Trigger turn end events for passives that need end-of-turn processing."""
        counts = Counter(target.passives)
        for pid, count in counts.items():
            cls = self._registry.get(pid)
            if cls is None:
                continue
            passive_instance = cls()

            # Check if passive has turn end handling
            if hasattr(passive_instance, "on_turn_end"):
                stacks = min(count, getattr(cls, "max_stacks", count))
                for _ in range(stacks):
                    await passive_instance.on_turn_end(target)

    async def trigger_defeat(self, target) -> None:
        """Trigger defeat events for passives that need cleanup on defeat."""
        counts = Counter(target.passives)
        for pid, count in counts.items():
            cls = self._registry.get(pid)
            if cls is None:
                continue
            passive_instance = cls()

            # Check if passive has defeat handling
            if hasattr(passive_instance, "on_defeat"):
                stacks = min(count, getattr(cls, "max_stacks", count))
                for _ in range(stacks):
                    await passive_instance.on_defeat(target)

    async def trigger_hit_landed(
        self, attacker, target, damage: int = 0, action_type: str = "attack", **kwargs
    ) -> None:
        """Trigger passives when a hit successfully lands."""
        counts = Counter(attacker.passives)
        for pid, count in counts.items():
            cls = self._registry.get(pid)
            if cls is None or getattr(cls, "trigger", None) != "hit_landed":
                continue

            passive_instance = cls()

            # Special handling for hit-based passives
            if hasattr(passive_instance, "on_hit_landed"):
                stacks = min(count, getattr(cls, "max_stacks", count))
                for _ in range(stacks):
                    await passive_instance.on_hit_landed(
                        attacker, target, damage, action_type, **kwargs
                    )

            # Regular passive application with enhanced context
            stacks = min(count, getattr(cls, "max_stacks", count))
            for _ in range(stacks):
                try:
                    await passive_instance.apply(
                        attacker,
                        hit_target=target,
                        damage=damage,
                        action_type=action_type,
                        **kwargs,
                    )
                except TypeError:
                    # Fall back to simple apply for existing passives
                    await passive_instance.apply(attacker)

    async def trigger_turn_start(self, target, **kwargs) -> None:
        """Trigger turn start events for passives that need turn initialization."""
        counts = Counter(target.passives)
        for pid, count in counts.items():
            cls = self._registry.get(pid)
            if cls is None:
                continue

            passive_instance = cls()

            # Special handling for turn start passives
            if getattr(cls, "trigger", None) == "turn_start" and hasattr(
                passive_instance, "on_turn_start"
            ):
                stacks = min(count, getattr(cls, "max_stacks", count))
                for _ in range(stacks):
                    await passive_instance.on_turn_start(target, **kwargs)

            # Regular passive application only for turn_start passives; be lenient with kwargs
            if getattr(cls, "trigger", None) == "turn_start":
                stacks = min(count, getattr(cls, "max_stacks", count))
                for _ in range(stacks):
                    try:
                        await passive_instance.apply(target, **kwargs)
                    except TypeError:
                        await passive_instance.apply(target)

    async def trigger_level_up(self, target, **kwargs) -> None:
        """Trigger level up events for passives that respond to leveling."""
        counts = Counter(target.passives)
        for pid, count in counts.items():
            cls = self._registry.get(pid)
            if cls is None or getattr(cls, "trigger", None) != "level_up":
                continue

            passive_instance = cls()

            # Special handling for level up passives
            if hasattr(passive_instance, "on_level_up"):
                stacks = min(count, getattr(cls, "max_stacks", count))
                for _ in range(stacks):
                    await passive_instance.on_level_up(target, **kwargs)

            # Regular passive application
            stacks = min(count, getattr(cls, "max_stacks", count))
            for _ in range(stacks):
                try:
                    await passive_instance.apply(target, **kwargs)
                except TypeError:
                    try:
                        await passive_instance.apply(target)
                    except TypeError:
                        log.warning("Passive %s incompatible with level_up kwargs", pid)

    def describe(self, target) -> list[dict[str, Any]]:
        """Return structured information for a target's passives."""
        info: list[dict[str, Any]] = []
        counts = Counter(getattr(target, "passives", []))
        for pid, count in counts.items():
            cls = self._registry.get(pid)
            if cls is None:
                info.append(
                    {
                        "id": pid,
                        "name": pid,
                        "stacks": count,
                        "max_stacks": None,
                        "display": "spinner",
                    }
                )
                continue

            stacks = count
            if hasattr(cls, "get_stacks"):
                try:
                    stacks = cls.get_stacks(target)  # type: ignore[attr-defined]
                except Exception:
                    stacks = count

            max_stacks = getattr(cls, "max_stacks", None)

            display = getattr(cls, "stack_display", None)
            if hasattr(cls, "get_display"):
                try:
                    display = cls.get_display(target)  # type: ignore[attr-defined]
                except Exception:
                    pass
            if display is None:
                if max_stacks == 1:
                    display = "spinner"
                elif max_stacks is None or max_stacks <= 5:
                    display = "pips"
                else:
                    display = "number"

            info.append(
                {
                    "id": pid,
                    "name": getattr(cls, "name", pid),
                    "stacks": stacks,
                    "max_stacks": max_stacks,
                    "display": display,
                }
            )
        return info
