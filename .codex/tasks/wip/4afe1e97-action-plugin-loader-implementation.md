# Task: Action Plugin Loader Implementation

**Status:** WIP  
**Priority:** High  
**Category:** Implementation  
**Goal File:** `.codex/tasks/wip/GOAL-action-plugin-system.md`

## Objective

Implement the action plugin discovery and registration system that integrates with the existing plugin loader infrastructure, enabling automatic discovery and management of action plugins.

## Background

The game already has a plugin system (`backend/plugins/plugin_loader.py`) that discovers and registers plugins for characters, passives, cards, relics, etc. This task extends that system to support action plugins.

## Prerequisites

- [ ] `9a56e7d1-action-plugin-architecture-design.md` - Architecture design completed
- [ ] Action base classes defined (`ActionBase`, `ActionResult`, `BattleContext`)

## Requirements

### 1. Extend PluginLoader for Actions

**File:** `backend/plugins/plugin_loader.py`

Add action plugin support to the existing plugin loader:

```python
# Add to PLUGIN_DIRS or equivalent
PLUGIN_DIRS = {
    "characters": "backend/plugins/characters",
    "passives": "backend/plugins/passives",
    "cards": "backend/plugins/cards",
    "relics": "backend/plugins/relics",
    "actions": "backend/plugins/actions",  # NEW
    # ... other categories
}
```

Ensure that:
- Action plugins are discovered recursively in `backend/plugins/actions/`
- Classes with `plugin_type = "action"` are registered
- Event bus is injected into action plugins
- Base classes are included but can be filtered out

### 2. Create ActionRegistry

**File:** `backend/plugins/actions/registry.py`

Implement a singleton action registry:

```python
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from plugins.actions._base import ActionBase


class ActionRegistry:
    """Central registry for managing action plugins."""
    
    _instance: ActionRegistry | None = None
    _actions: dict[str, ActionBase] = {}
    _actions_by_type: dict[str, list[ActionBase]] = {}
    _character_actions: dict[str, list[ActionBase]] = {}
    
    def __new__(cls) -> ActionRegistry:
        """Ensure singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._actions = {}
            cls._instance._actions_by_type = {}
            cls._instance._character_actions = {}
        return cls._instance
    
    def register_action(self, action: ActionBase) -> None:
        """Register an action plugin.
        
        Args:
            action: The action plugin instance to register
            
        Raises:
            ValueError: If action ID is already registered
        """
        action_id = getattr(action, "id", None)
        if not action_id:
            raise ValueError(f"Action {action} has no id attribute")
        
        if action_id in self._actions:
            # Log warning but allow override (for hot-reloading)
            import logging
            log = logging.getLogger(__name__)
            log.warning(f"Action {action_id} already registered, overriding")
        
        self._actions[action_id] = action
        
        # Register by action type
        action_type = getattr(action, "action_type", "unknown")
        if action_type not in self._actions_by_type:
            self._actions_by_type[action_type] = []
        if action not in self._actions_by_type[action_type]:
            self._actions_by_type[action_type].append(action)
        
        # Register character-specific actions
        character_id = getattr(action, "character_id", None)
        if character_id:
            if character_id not in self._character_actions:
                self._character_actions[character_id] = []
            if action not in self._character_actions[character_id]:
                self._character_actions[character_id].append(action)
    
    def get_action(self, action_id: str) -> ActionBase | None:
        """Get an action plugin by ID.
        
        Args:
            action_id: The unique identifier for the action
            
        Returns:
            The action plugin instance, or None if not found
        """
        return self._actions.get(action_id)
    
    def get_actions_by_type(self, action_type: str) -> list[ActionBase]:
        """Get all actions of a specific type.
        
        Args:
            action_type: The action type (e.g., "normal_attack", "special", "ultimate")
            
        Returns:
            List of action plugins of that type
        """
        return self._actions_by_type.get(action_type, []).copy()
    
    def get_character_actions(self, character_id: str) -> list[ActionBase]:
        """Get all actions available to a specific character.
        
        Args:
            character_id: The character's unique identifier
            
        Returns:
            List of action plugins for that character
        """
        # Get character-specific actions
        char_actions = self._character_actions.get(character_id, []).copy()
        
        # Add universal actions (normal attack, etc.)
        universal_actions = self.get_actions_by_type("normal_attack")
        for action in universal_actions:
            if action not in char_actions:
                char_actions.append(action)
        
        return char_actions
    
    def get_all_actions(self) -> dict[str, ActionBase]:
        """Get all registered actions.
        
        Returns:
            Dictionary mapping action IDs to action instances
        """
        return self._actions.copy()
    
    def clear(self) -> None:
        """Clear all registered actions (useful for testing)."""
        self._actions.clear()
        self._actions_by_type.clear()
        self._character_actions.clear()


# Module-level accessor
_registry: ActionRegistry | None = None


def get_action_registry() -> ActionRegistry:
    """Get the singleton action registry instance."""
    global _registry
    if _registry is None:
        _registry = ActionRegistry()
    return _registry


def register_action(action: ActionBase) -> None:
    """Convenience function to register an action."""
    get_action_registry().register_action(action)
```

### 3. Create Action Plugin Initialization

**File:** `backend/plugins/actions/__init__.py`

Set up action plugin discovery and registration:

```python
"""Action plugin system for combat actions."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from plugins.plugin_loader import PluginLoader

from .registry import get_action_registry
from .registry import register_action

if TYPE_CHECKING:
    from ._base import ActionBase


log = logging.getLogger(__name__)


def discover_actions() -> dict[str, type[ActionBase]]:
    """Discover and load all action plugins.
    
    Returns:
        Dictionary mapping action IDs to action classes
    """
    loader = PluginLoader()
    loader.discover("backend/plugins/actions")
    
    actions = loader.get_plugins("action")
    log.info(f"Discovered {len(actions)} action plugins")
    
    return actions


def initialize_action_registry() -> None:
    """Initialize the action registry with discovered plugins."""
    registry = get_action_registry()
    registry.clear()  # Clear any existing registrations
    
    action_classes = discover_actions()
    
    for action_id, action_class in action_classes.items():
        try:
            # Instantiate the action (assumes dataclass with defaults)
            action_instance = action_class()
            registry.register_action(action_instance)
            log.debug(f"Registered action: {action_id}")
        except Exception as e:
            log.error(f"Failed to register action {action_id}: {e}")
            continue
    
    log.info(f"Action registry initialized with {len(registry.get_all_actions())} actions")


__all__ = [
    "discover_actions",
    "initialize_action_registry",
    "get_action_registry",
    "register_action",
]
```

### 4. Integrate with Application Startup

**File:** `backend/app.py` or equivalent startup file

Add action plugin initialization:

```python
# Add to application startup sequence
from plugins.actions import initialize_action_registry

# ... other initialization code ...

# Initialize action plugins
try:
    initialize_action_registry()
    log.info("Action plugin system initialized")
except Exception as e:
    log.error(f"Failed to initialize action plugins: {e}")
    # Decide if this should be fatal or not
```

### 5. Create Helper Functions

**File:** `backend/plugins/actions/utils.py`

Provide utility functions for working with actions:

```python
"""Utility functions for action plugins."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .registry import get_action_registry

if TYPE_CHECKING:
    from autofighter.stats import Stats
    from ._base import ActionBase


def get_default_action(actor: Stats) -> ActionBase | None:
    """Get the default action for an actor (usually normal attack).
    
    Args:
        actor: The acting combatant
        
    Returns:
        The default action plugin, or None if not found
    """
    registry = get_action_registry()
    return registry.get_action("normal_attack")


def get_character_action(character_id: str, action_id: str) -> ActionBase | None:
    """Get a specific action for a character.
    
    Args:
        character_id: The character's unique identifier
        action_id: The action's unique identifier
        
    Returns:
        The action plugin, or None if not found or not available to character
    """
    registry = get_action_registry()
    char_actions = registry.get_character_actions(character_id)
    
    for action in char_actions:
        if getattr(action, "id", None) == action_id:
            return action
    
    return None


def list_available_actions(actor: Stats) -> list[ActionBase]:
    """List all actions available to an actor.
    
    Args:
        actor: The acting combatant
        
    Returns:
        List of available action plugins
    """
    registry = get_action_registry()
    character_id = getattr(actor, "id", None)
    
    if character_id:
        return registry.get_character_actions(character_id)
    
    # Fallback: return only normal attack
    normal_attack = registry.get_action("normal_attack")
    return [normal_attack] if normal_attack else []
```

## Implementation Steps

1. **Extend plugin loader**:
   - [ ] Add "actions" to plugin categories
   - [ ] Verify discovery works for action plugins
   - [ ] Test with a dummy action plugin

2. **Implement ActionRegistry**:
   - [ ] Create registry.py with all methods
   - [ ] Add comprehensive docstrings
   - [ ] Include error handling

3. **Create initialization code**:
   - [ ] Implement `__init__.py` for actions package
   - [ ] Add discovery function
   - [ ] Add initialization function

4. **Integrate with app startup**:
   - [ ] Find correct initialization point
   - [ ] Add action registry initialization
   - [ ] Handle initialization errors gracefully

5. **Create utility functions**:
   - [ ] Implement utils.py
   - [ ] Add helper functions for common operations
   - [ ] Document usage patterns

6. **Add tests**:
   - [ ] Test action discovery
   - [ ] Test registration
   - [ ] Test retrieval by ID, type, character
   - [ ] Test error cases

## Testing Strategy

### Unit Tests

**File:** `backend/tests/test_action_registry.py`

```python
import pytest
from plugins.actions.registry import ActionRegistry
from plugins.actions._base import ActionBase
from dataclasses import dataclass


@dataclass
class MockAction(ActionBase):
    plugin_type = "action"
    id: str = "mock_action"
    name: str = "Mock Action"
    action_type: str = "test"


def test_registry_singleton():
    """Test that registry is a singleton."""
    registry1 = ActionRegistry()
    registry2 = ActionRegistry()
    assert registry1 is registry2


def test_register_action():
    """Test action registration."""
    registry = ActionRegistry()
    registry.clear()
    
    action = MockAction()
    registry.register_action(action)
    
    assert registry.get_action("mock_action") is action


def test_get_actions_by_type():
    """Test retrieving actions by type."""
    registry = ActionRegistry()
    registry.clear()
    
    action = MockAction()
    registry.register_action(action)
    
    actions = registry.get_actions_by_type("test")
    assert len(actions) == 1
    assert actions[0] is action


def test_character_actions():
    """Test character-specific action registration."""
    # Test implementation
    pass


def test_registry_clear():
    """Test clearing the registry."""
    # Test implementation
    pass
```

### Integration Tests

**File:** `backend/tests/test_action_loader.py`

```python
def test_discover_actions():
    """Test that actions are discovered from plugins directory."""
    # Test implementation
    pass


def test_initialize_registry():
    """Test registry initialization."""
    # Test implementation
    pass


def test_action_available_in_battle():
    """Test that registered actions can be used in battle."""
    # Test implementation
    pass
```

## Acceptance Criteria

- [ ] ActionRegistry class implemented with all required methods
- [ ] Action discovery integrated with PluginLoader
- [ ] Action initialization added to application startup
- [ ] Utility functions created and documented
- [ ] All tests passing (minimum 10 tests)
- [ ] Code passes linting (`uvx ruff check`)
- [ ] Documentation updated
- [ ] Can register and retrieve actions successfully
- [ ] Registry works in actual battle context

## Dependencies

- Action plugin architecture design
- Action base classes (_base.py, result.py, context.py)

## Estimated Effort

- Implementation: 6-8 hours
- Testing: 3-4 hours
- Integration: 2-3 hours
- Documentation: 2 hours
- **Total: ~13-17 hours**

## Notes

- Follow existing plugin loader patterns for consistency
- Ensure thread-safety if needed
- Consider hot-reloading for development
- Make sure registry is initialized before any battles start
- Add logging for debugging action registration issues
- Consider caching action lookups for performance
