"""Tests for BasicAttackAction plugin."""

from __future__ import annotations

import pytest

from autofighter.stats import Stats
from plugins.actions.context import BattleContext
from plugins.actions.normal.basic_attack import BasicAttackAction
from plugins.actions.registry import ActionRegistry


@pytest.fixture
def mock_actor() -> Stats:
    """Create a mock actor for testing."""
    actor = Stats()
    actor.id = "test_actor"
    actor.hp = 100
    actor.max_hp = 100
    actor.atk = 15
    actor.defense = 5
    actor.action_points = 3
    return actor


@pytest.fixture
def mock_target() -> Stats:
    """Create a mock target for testing."""
    target = Stats()
    target.id = "test_target"
    target.hp = 80
    target.max_hp = 80
    target.atk = 8
    target.defense = 4
    return target


@pytest.fixture
def battle_context(mock_actor: Stats, mock_target: Stats) -> BattleContext:
    """Create a minimal battle context for testing."""
    from autofighter import stats as stats_module
    from autofighter.passives import PassiveRegistry

    # Set battle as active
    stats_module._BATTLE_ACTIVE = True

    context = BattleContext(
        turn=1,
        run_id="test_run",
        phase="player",
        actor=mock_actor,
        allies=[mock_actor],
        enemies=[mock_target],
        action_registry=ActionRegistry(),
        passive_registry=PassiveRegistry(),
        effect_managers={},
    )

    yield context

    # Clean up - set battle as inactive
    stats_module._BATTLE_ACTIVE = False


@pytest.fixture
def basic_attack() -> BasicAttackAction:
    """Create a BasicAttackAction instance."""
    return BasicAttackAction()


def test_basic_attack_metadata(basic_attack: BasicAttackAction) -> None:
    """Test that BasicAttackAction has correct metadata."""
    assert basic_attack.id == "normal.basic_attack"
    assert basic_attack.name == "Basic Attack"
    assert basic_attack.plugin_type == "action"
    assert "normal_attack" in basic_attack.tags


@pytest.mark.asyncio
async def test_basic_attack_can_execute(
    basic_attack: BasicAttackAction,
    battle_context: BattleContext,
    mock_actor: Stats,
    mock_target: Stats,
) -> None:
    """Test that can_execute returns True when conditions are met."""
    can_execute = await basic_attack.can_execute(
        mock_actor,
        [mock_target],
        battle_context,
    )

    assert can_execute is True


@pytest.mark.asyncio
async def test_basic_attack_cannot_execute_no_targets(
    basic_attack: BasicAttackAction,
    battle_context: BattleContext,
    mock_actor: Stats,
) -> None:
    """Test that can_execute returns False with no targets."""
    can_execute = await basic_attack.can_execute(
        mock_actor,
        [],
        battle_context,
    )

    assert can_execute is False


@pytest.mark.asyncio
async def test_basic_attack_cannot_execute_insufficient_action_points(
    basic_attack: BasicAttackAction,
    battle_context: BattleContext,
    mock_actor: Stats,
    mock_target: Stats,
) -> None:
    """Test that can_execute returns False without action points."""
    mock_actor.action_points = 0

    can_execute = await basic_attack.can_execute(
        mock_actor,
        [mock_target],
        battle_context,
    )

    assert can_execute is False


@pytest.mark.asyncio
async def test_basic_attack_execute_success(
    basic_attack: BasicAttackAction,
    battle_context: BattleContext,
    mock_actor: Stats,
    mock_target: Stats,
) -> None:
    """Test that execute deals damage to target."""
    initial_hp = mock_target.hp
    target_id = mock_target.id

    result = await basic_attack.execute(
        mock_actor,
        [mock_target],
        battle_context,
    )

    assert result.success is True
    assert target_id in result.damage_dealt
    assert result.damage_dealt[target_id] > 0
    assert mock_target.hp < initial_hp


@pytest.mark.asyncio
async def test_basic_attack_execute_no_targets(
    basic_attack: BasicAttackAction,
    battle_context: BattleContext,
    mock_actor: Stats,
) -> None:
    """Test that execute fails gracefully with no targets."""
    result = await basic_attack.execute(
        mock_actor,
        [],
        battle_context,
    )

    assert result.success is False
    assert len(result.messages) > 0


@pytest.mark.asyncio
async def test_basic_attack_run_with_cost_deduction(
    basic_attack: BasicAttackAction,
    battle_context: BattleContext,
    mock_actor: Stats,
    mock_target: Stats,
) -> None:
    """Test that run() deducts action points after execution."""
    initial_action_points = mock_actor.action_points

    result = await basic_attack.run(
        mock_actor,
        [mock_target],
        battle_context,
    )

    assert result.success is True
    assert mock_actor.action_points == initial_action_points - 1


@pytest.mark.asyncio
async def test_basic_attack_metadata_tracking(
    basic_attack: BasicAttackAction,
    battle_context: BattleContext,
    mock_actor: Stats,
    mock_target: Stats,
) -> None:
    """Test that execute tracks metadata properly."""
    result = await basic_attack.execute(
        mock_actor,
        [mock_target],
        battle_context,
    )

    assert "damage_type" in result.metadata
    assert "targets_hit" in result.metadata
    assert "attack_index" in result.metadata
    assert "attack_total" in result.metadata
    assert "attack_sequence" in result.metadata


@pytest.mark.asyncio
async def test_basic_attack_get_valid_targets(
    basic_attack: BasicAttackAction,
    mock_actor: Stats,
    mock_target: Stats,
) -> None:
    """Test that get_valid_targets filters correctly."""
    # Create a dead target
    dead_target = Stats()
    dead_target.id = "dead_target"
    dead_target.hp = 0

    valid_targets = basic_attack.get_valid_targets(
        mock_actor,
        allies=[mock_actor],
        enemies=[mock_target, dead_target],
    )

    assert mock_target in valid_targets
    assert dead_target not in valid_targets


@pytest.mark.asyncio
async def test_basic_attack_animation_plan(
    basic_attack: BasicAttackAction,
) -> None:
    """Test that animation plan is configured."""
    assert basic_attack.animation.name == "basic_attack"
    assert basic_attack.animation.duration > 0
    assert basic_attack.animation.per_target > 0
