"""Helper functions for guidebook routes."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from plugins.damage_types import ALL_DAMAGE_TYPES


def _load_damage_type_class(name: str):
    """Load damage type class by name.

    Args:
        name: Damage type name

    Returns:
        Damage type class
    """
    try:
        module = import_module(f"plugins.damage_types.{name.lower()}")
        return getattr(module, name)
    except Exception:
        module = import_module("plugins.damage_types.generic")
        return module.Generic


def _compute_strong_against_map() -> dict[str, list[str]]:
    """Compute elemental advantage relationships.

    Returns:
        Dictionary mapping attacker types to list of weak target types
    """
    all_types = list(ALL_DAMAGE_TYPES)
    weakness_by_type: dict[str, str] = {}

    for name in all_types:
        cls = _load_damage_type_class(name)
        weakness = getattr(cls, "weakness", None)
        if isinstance(weakness, str) and weakness.lower() != "none":
            weakness_by_type[name] = weakness

    strong_map: dict[str, list[str]] = {}
    for type_name, weakness in weakness_by_type.items():
        strong_map.setdefault(weakness, []).append(type_name)

    for attacker in strong_map:
        strong_map[attacker].sort()

    return strong_map


def _elemental_resistance_summary() -> str:
    """Generate human-readable summary of elemental relationships.

    Returns:
        Comma-separated string of relationships (e.g., "Fire→Ice, Ice→Wind")
    """
    strong_map = _compute_strong_against_map()

    primary_order = ["Fire", "Ice", "Lightning", "Wind"]
    relationships: list[str] = []

    for attacker in primary_order:
        for target in strong_map.get(attacker, []):
            relationships.append(f"{attacker}→{target}")

    light_targets = set(strong_map.get("Light", []))
    dark_targets = set(strong_map.get("Dark", []))
    if "Dark" in light_targets and "Light" in dark_targets:
        relationships.append("Light↔Dark")
    else:
        for target in sorted(light_targets):
            relationships.append(f"Light→{target}")
        for target in sorted(dark_targets):
            relationships.append(f"Dark→{target}")

    handled = set(primary_order + ["Light", "Dark"])
    remaining = sorted(name for name in strong_map if name not in handled)
    for attacker in remaining:
        for target in strong_map[attacker]:
            relationships.append(f"{attacker}→{target}")

    return ", ".join(relationships)


def _plugin_description(cls) -> str:
    """Extract description from plugin class.

    Args:
        cls: Plugin class

    Returns:
        Description string
    """
    try:
        return cls.get_description()
    except NotImplementedError:
        doc = getattr(cls, "__doc__", None)
        if doc:
            return doc.strip()
        return cls.__name__.replace("_", " ").title()


def _serialize_stat_plugins(entries: dict[str, type]) -> list[dict[str, Any]]:
    """Serialize stat effect plugins to JSON-friendly format.

    Args:
        entries: Dictionary mapping effect IDs to plugin classes

    Returns:
        List of serialized effect dictionaries
    """
    serialized: list[dict[str, Any]] = []
    for effect_id, cls in sorted(entries.items()):
        try:
            instance = cls()
        except Exception:
            # Skip malformed plugins but log later if necessary
            continue
        serialized.append(
            {
                "id": effect_id,
                "name": getattr(instance, "name", effect_id.replace("_", " ").title()),
                "description": _plugin_description(cls),
                "stack_display": getattr(instance, "stack_display", "pips"),
                "max_stacks": getattr(instance, "max_stacks", None),
                "default_duration": getattr(instance, "duration", -1),
                "stat_modifiers": dict(getattr(instance, "stat_modifiers", {})),
            }
        )
    return serialized
