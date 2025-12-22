"""Tests for ActionRegistry."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from autofighter.stats import Stats
from plugins.actions import ActionBase, ActionType
from plugins.actions.registry import ActionRegistry
from plugins.actions.result import ActionResult


@dataclass(kw_only=True, slots=True)
class MockAction(ActionBase):
    """Mock action for testing."""

    id: str = "test.mock_action"
    name: str = "Mock Action"
    description: str = "A test action"
    action_type: ActionType = ActionType.NORMAL
    tags: tuple[str, ...] = ("test",)

    async def execute(self, actor, targets, context) -> ActionResult:
        return ActionResult(success=True)


@dataclass(kw_only=True, slots=True)
class MockSpecialAction(ActionBase):
    """Mock special action for testing."""

    id: str = "test.special_action"
    name: str = "Special Action"
    description: str = "A test special action"
    action_type: ActionType = ActionType.SPECIAL
    cooldown_turns: int = 3

    async def execute(self, actor, targets, context) -> ActionResult:
        return ActionResult(success=True)


@pytest.fixture
def registry() -> ActionRegistry:
    """Create a fresh ActionRegistry."""
    return ActionRegistry()


@pytest.fixture
def mock_actor() -> Stats:
    """Create a mock actor."""
    actor = Stats()
    actor.id = "test_actor"
    actor.hp = 100
    actor.action_points = 3
    return actor


def test_registry_register_action(registry: ActionRegistry) -> None:
    """Test that actions can be registered."""
    registry.register_action(MockAction)

    assert "test.mock_action" in registry._actions
    assert registry.get_action_class("test.mock_action") == MockAction


def test_registry_register_duplicate_action_raises(registry: ActionRegistry) -> None:
    """Test that duplicate registration raises ValueError."""
    registry.register_action(MockAction)

    with pytest.raises(ValueError, match="Duplicate action id"):
        registry.register_action(MockAction)


def test_registry_register_non_action_raises(registry: ActionRegistry) -> None:
    """Test that non-action classes raise ValueError."""

    class NotAnAction:
        pass

    with pytest.raises(ValueError, match="not an action plugin"):
        registry.register_action(NotAnAction)  # type: ignore


def test_registry_instantiate(registry: ActionRegistry) -> None:
    """Test that actions can be instantiated."""
    registry.register_action(MockAction)

    action = registry.instantiate("test.mock_action")

    assert isinstance(action, MockAction)
    assert action.id == "test.mock_action"


def test_registry_instantiate_unknown_raises(registry: ActionRegistry) -> None:
    """Test that unknown action ID raises KeyError."""
    with pytest.raises(KeyError, match="Unknown action id"):
        registry.instantiate("nonexistent.action")


def test_registry_get_actions_by_type(registry: ActionRegistry) -> None:
    """Test that actions can be retrieved by type."""
    registry.register_action(MockAction)
    registry.register_action(MockSpecialAction)

    normal_actions = registry.get_actions_by_type(ActionType.NORMAL)
    special_actions = registry.get_actions_by_type(ActionType.SPECIAL)

    assert len(normal_actions) == 1
    assert MockAction in normal_actions
    assert len(special_actions) == 1
    assert MockSpecialAction in special_actions


def test_registry_get_character_actions(registry: ActionRegistry) -> None:
    """Test that character-specific actions can be registered and retrieved."""
    registry.register_action(MockAction)
    registry.register_action(MockSpecialAction)

    registry.register_character_actions(
        "test_character",
        ["test.mock_action", "test.special_action"],
    )

    char_actions = registry.get_character_actions("test_character")

    assert len(char_actions) == 2
    assert MockAction in char_actions
    assert MockSpecialAction in char_actions


def test_registry_cooldown_tracking(
    registry: ActionRegistry,
    mock_actor: Stats,
) -> None:
    """Test that cooldowns are tracked correctly."""
    registry.register_action(MockSpecialAction)
    action = registry.instantiate("test.special_action")

    # Should be available initially
    assert registry.is_available(mock_actor, action) is True

    # Start cooldown
    registry.start_cooldown(mock_actor, action)

    # Should not be available now
    assert registry.is_available(mock_actor, action) is False


def test_registry_advance_cooldowns(
    registry: ActionRegistry,
    mock_actor: Stats,
) -> None:
    """Test that cooldowns advance correctly."""
    registry.register_action(MockSpecialAction)
    action = registry.instantiate("test.special_action")

    # Start cooldown (3 turns)
    registry.start_cooldown(mock_actor, action)
    assert registry.is_available(mock_actor, action) is False

    # Advance one turn
    registry.advance_cooldowns()
    assert registry.is_available(mock_actor, action) is False

    # Advance two more turns
    registry.advance_cooldowns()
    registry.advance_cooldowns()

    # Should be available now
    assert registry.is_available(mock_actor, action) is True


def test_registry_reset_actor(
    registry: ActionRegistry,
    mock_actor: Stats,
) -> None:
    """Test that actor cooldowns can be reset."""
    registry.register_action(MockSpecialAction)
    action = registry.instantiate("test.special_action")

    # Start cooldown
    registry.start_cooldown(mock_actor, action)
    assert registry.is_available(mock_actor, action) is False

    # Reset actor
    registry.reset_actor(mock_actor)

    # Should be available now
    assert registry.is_available(mock_actor, action) is True


def test_registry_shared_cooldown_tags(
    registry: ActionRegistry,
    mock_actor: Stats,
) -> None:
    """Test that actions with shared tags share cooldowns."""

    @dataclass(kw_only=True, slots=True)
    class MockActionA(ActionBase):
        id: str = "test.action_a"
        name: str = "Action A"
        description: str = "Test action A"
        action_type: ActionType = ActionType.NORMAL
        tags: tuple[str, ...] = ("shared_cooldown",)
        cooldown_turns: int = 2

        async def execute(self, actor, targets, context) -> ActionResult:
            return ActionResult(success=True)

    @dataclass(kw_only=True, slots=True)
    class MockActionB(ActionBase):
        id: str = "test.action_b"
        name: str = "Action B"
        description: str = "Test action B"
        action_type: ActionType = ActionType.NORMAL
        tags: tuple[str, ...] = ("shared_cooldown",)
        cooldown_turns: int = 2

        async def execute(self, actor, targets, context) -> ActionResult:
            return ActionResult(success=True)

    registry.register_action(MockActionA)
    registry.register_action(MockActionB)

    action_a = registry.instantiate("test.action_a")
    action_b = registry.instantiate("test.action_b")

    # Both should be available
    assert registry.is_available(mock_actor, action_a) is True
    assert registry.is_available(mock_actor, action_b) is True

    # Use action A
    registry.start_cooldown(mock_actor, action_a)

    # Both should be on cooldown due to shared tag
    assert registry.is_available(mock_actor, action_a) is False
    assert registry.is_available(mock_actor, action_b) is False
