"""Utility functions for action plugins."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .registry import ActionRegistry

if TYPE_CHECKING:
    from autofighter.stats import Stats

    from ._base import ActionBase


def get_default_action(registry: ActionRegistry) -> ActionBase | None:
    """Get the default action (usually normal attack).

    Args:
        registry: The ActionRegistry instance

    Returns:
        The default action plugin, or None if not found
    """
    try:
        return registry.instantiate("normal.basic_attack")
    except KeyError:
        return None


def get_character_action(
    registry: ActionRegistry,
    character_id: str,
    action_id: str,
) -> ActionBase | None:
    """Get a specific action for a character.

    Args:
        registry: The ActionRegistry instance
        character_id: The character's unique identifier
        action_id: The action's unique identifier

    Returns:
        The action plugin, or None if not found or not available to character
    """
    char_actions = registry.get_character_actions(character_id)

    for action_class in char_actions:
        # Instantiate to get the ID
        try:
            action = action_class()
            if action.id == action_id:
                return action
        except Exception:
            continue

    return None


def list_available_actions(
    registry: ActionRegistry,
    actor: Stats,
) -> list[ActionBase]:
    """List all actions available to an actor.

    Args:
        registry: The ActionRegistry instance
        actor: The acting combatant

    Returns:
        List of available action plugin instances
    """
    character_id = getattr(actor, "id", None)

    if character_id:
        action_classes = registry.get_character_actions(character_id)
        actions = []
        for action_class in action_classes:
            try:
                actions.append(action_class())
            except Exception:
                continue
        return actions

    # Fallback: return only normal attack
    default_action = get_default_action(registry)
    return [default_action] if default_action else []
