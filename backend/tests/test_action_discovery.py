"""Tests for action plugin auto-discovery system."""

from __future__ import annotations

from plugins.actions import ActionRegistry
from plugins.actions import discover
from plugins.actions import initialize_action_registry
from plugins.actions.utils import get_character_action
from plugins.actions.utils import get_default_action
from plugins.actions.utils import list_available_actions


def test_discover_actions():
    """Test that action plugins are discovered from the actions directory."""
    action_classes = discover()

    # Should discover at least the basic attack action
    assert len(action_classes) > 0
    assert "normal.basic_attack" in action_classes

    # All discovered plugins should have plugin_type = "action"
    for action_id, action_class in action_classes.items():
        assert getattr(action_class, "plugin_type", None) == "action"


def test_initialize_action_registry():
    """Test that the action registry is initialized with discovered plugins."""
    registry = initialize_action_registry()

    # Should have registered at least one action
    normal_actions = registry.get_actions_by_type("normal")
    assert len(normal_actions) > 0

    # Should be able to instantiate the basic attack
    basic_attack = registry.instantiate("normal.basic_attack")
    assert basic_attack.id == "normal.basic_attack"
    assert basic_attack.name == "Basic Attack"


def test_initialize_action_registry_with_existing_instance():
    """Test that initialization can use an existing registry instance."""
    registry = ActionRegistry()
    initialized_registry = initialize_action_registry(registry)

    # Should return the same instance
    assert initialized_registry is registry

    # Should have registered actions
    normal_actions = registry.get_actions_by_type("normal")
    assert len(normal_actions) > 0


def test_initialize_action_registry_idempotent():
    """Test that multiple initializations don't cause issues."""
    registry1 = initialize_action_registry()
    registry2 = initialize_action_registry()

    # Both should have the same actions registered
    actions1 = registry1.get_actions_by_type("normal")
    actions2 = registry2.get_actions_by_type("normal")

    assert len(actions1) == len(actions2)


def test_get_default_action():
    """Test getting the default action."""
    registry = initialize_action_registry()
    default_action = get_default_action(registry)

    assert default_action is not None
    assert default_action.id == "normal.basic_attack"


def test_get_default_action_empty_registry():
    """Test getting default action from empty registry."""
    registry = ActionRegistry()
    default_action = get_default_action(registry)

    assert default_action is None


def test_get_character_action():
    """Test getting a character-specific action."""
    registry = initialize_action_registry()

    # Register character actions
    registry.register_character_actions("luna", ["normal.basic_attack"])

    # Get the action for the character
    action = get_character_action(registry, "luna", "normal.basic_attack")

    assert action is not None
    assert action.id == "normal.basic_attack"


def test_get_character_action_not_found():
    """Test getting a non-existent character action."""
    registry = initialize_action_registry()

    action = get_character_action(registry, "unknown_character", "unknown_action")

    assert action is None


def test_list_available_actions():
    """Test listing available actions for an actor."""
    from unittest.mock import MagicMock

    registry = initialize_action_registry()
    registry.register_character_actions("luna", ["normal.basic_attack"])

    # Create a mock actor with character ID
    actor = MagicMock()
    actor.id = "luna"

    actions = list_available_actions(registry, actor)

    assert len(actions) > 0
    assert any(a.id == "normal.basic_attack" for a in actions)


def test_list_available_actions_no_character_id():
    """Test listing actions for actor without character ID."""
    from unittest.mock import MagicMock

    registry = initialize_action_registry()

    # Create a mock actor without character ID
    actor = MagicMock()
    del actor.id

    actions = list_available_actions(registry, actor)

    # Should return at least the default action
    assert len(actions) >= 1


def test_list_available_actions_with_id_but_no_loadout():
    """Test that actors with id but no registered loadout get default action."""
    from unittest.mock import MagicMock

    registry = initialize_action_registry()

    # Create a mock actor with character ID but no registered actions
    actor = MagicMock()
    actor.id = "unknown_character_with_id"

    actions = list_available_actions(registry, actor)

    # Should return at least the default action (fallback)
    assert len(actions) >= 1
    assert any(a.id == "normal.basic_attack" for a in actions)


def test_discover_caches_results():
    """Test that discover() caches results for efficiency."""
    # First call
    actions1 = discover()

    # Second call should return the same cached result
    actions2 = discover()

    assert actions1 is actions2


def test_action_plugin_metadata():
    """Test that discovered actions have required metadata."""
    action_classes = discover()

    for action_id, action_class in action_classes.items():
        # Instantiate to check metadata
        action = action_class()

        # All actions should have basic metadata
        assert hasattr(action, "id")
        assert hasattr(action, "name")
        assert hasattr(action, "description")
        assert hasattr(action, "action_type")
        assert hasattr(action, "targeting")
        assert hasattr(action, "cost")

        # ID should match the registry key
        assert action.id == action_id


def test_action_plugin_execute_method():
    """Test that all discovered actions implement execute method."""
    action_classes = discover()

    for action_class in action_classes.values():
        action = action_class()

        # Should have an execute method
        assert hasattr(action, "execute")
        assert callable(action.execute)
