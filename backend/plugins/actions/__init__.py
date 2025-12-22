"""Action plugin infrastructure package.

The loader-facing modules live here so follow-up tasks can import
`ActionBase`, `ActionRegistry`, and the shared context/result helpers from a
single place.  This makes it trivial for the battle turn loop to rely on the
new plugin ecosystem without reaching into private modules.
"""

from __future__ import annotations

import logging
from pathlib import Path

from plugins.plugin_loader import PluginLoader

from ._base import (
    ActionAnimationPlan,
    ActionBase,
    ActionCostBreakdown,
    ActionType,
    TargetingRules,
    TargetScope,
    TargetSide,
)
from .context import BattleContext
from .registry import ActionRegistry
from .result import ActionResult
from .special import SpecialAbilityBase
from .ultimate import UltimateActionBase

log = logging.getLogger(__name__)

ACTION_LOADER: PluginLoader | None = None
ACTION_REGISTRY: dict[str, type[ActionBase]] | None = None
INITIALIZED_ACTION_REGISTRY: ActionRegistry | None = None


def discover() -> dict[str, type[ActionBase]]:
    """Load action plugins once and return the registry.

    Returns:
        Dictionary mapping action IDs to action classes
    """
    global ACTION_LOADER
    global ACTION_REGISTRY

    if ACTION_REGISTRY is None:
        plugin_dir = Path(__file__).resolve().parent
        ACTION_LOADER = PluginLoader(required=["action"])
        ACTION_LOADER.discover(str(plugin_dir))
        raw_plugins = ACTION_LOADER.get_plugins("action")

        # Convert plugin_loader keys (which may be field descriptors for dataclasses)
        # to actual string IDs by instantiating each plugin
        ACTION_REGISTRY = {}
        for _, action_class in raw_plugins.items():
            try:
                # Instantiate to get the actual ID
                instance = action_class()
                actual_id = instance.id
                ACTION_REGISTRY[actual_id] = action_class
            except Exception as e:
                log.error(f"Failed to process action class {action_class}: {e}")
                continue

        log.info(f"Discovered {len(ACTION_REGISTRY)} action plugins")

    return ACTION_REGISTRY


def initialize_action_registry(registry: ActionRegistry | None = None) -> ActionRegistry:
    """Initialize the action registry with discovered plugins.

    Args:
        registry: Optional ActionRegistry instance to use. If None, creates a new one.

    Returns:
        The initialized ActionRegistry instance
    """
    global INITIALIZED_ACTION_REGISTRY

    if registry is None:
        registry = ActionRegistry()

    action_classes = discover()

    for action_id, action_class in action_classes.items():
        try:
            registry.register_action(action_class)
            log.debug(f"Registered action: {action_id}")
        except Exception as e:
            log.error(f"Failed to register action {action_id}: {e}")
            continue

    log.info(f"Action registry initialized with {len(action_classes)} actions")

    # Store the initialized registry globally
    INITIALIZED_ACTION_REGISTRY = registry

    return registry


def get_action_registry() -> ActionRegistry | None:
    """Get the globally initialized action registry.

    Returns:
        The initialized ActionRegistry instance, or None if not yet initialized
    """
    return INITIALIZED_ACTION_REGISTRY


__all__ = [
    "ActionAnimationPlan",
    "ActionBase",
    "ActionCostBreakdown",
    "ActionRegistry",
    "ActionResult",
    "ActionType",
    "SpecialAbilityBase",
    "BattleContext",
    "UltimateActionBase",
    "TargetScope",
    "TargetSide",
    "TargetingRules",
    "discover",
    "get_action_registry",
    "initialize_action_registry",
]
