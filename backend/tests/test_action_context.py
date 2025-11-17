"""Tests for BattleContext helper methods."""

from __future__ import annotations

import pytest

from autofighter.effects import EffectManager
from autofighter.stats import Stats
from plugins.actions.context import BattleContext
from plugins.actions.registry import ActionRegistry


@pytest.fixture
def mock_actor() -> Stats:
    """Create a mock actor for testing."""
    actor = Stats()
    actor.id = "test_actor"
    actor.hp = 100
    actor.max_hp = 100
    actor.atk = 10
    actor.defense = 5
    actor.action_points = 3
    actor.ultimate_charge = 0
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
    from autofighter.passives import PassiveRegistry
    from autofighter import stats as stats_module
    
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


@pytest.mark.asyncio
async def test_battle_context_apply_damage(
    battle_context: BattleContext,
    mock_actor: Stats,
    mock_target: Stats,
) -> None:
    """Test that BattleContext.apply_damage works correctly."""
    initial_hp = mock_target.hp
    damage_amount = 20.0

    damage_dealt = await battle_context.apply_damage(
        mock_actor,
        mock_target,
        damage_amount,
    )

    assert damage_dealt > 0
    assert mock_target.hp < initial_hp


@pytest.mark.asyncio
async def test_battle_context_apply_damage_with_metadata(
    battle_context: BattleContext,
    mock_actor: Stats,
    mock_target: Stats,
) -> None:
    """Test that metadata is properly staged for damage application."""
    metadata = {
        "attack_index": 1,
        "attack_total": 1,
        "attack_sequence": 1,
        "action_name": "Test Attack",
    }

    damage_dealt = await battle_context.apply_damage(
        mock_actor,
        mock_target,
        15.0,
        metadata=metadata,
    )

    assert damage_dealt > 0


@pytest.mark.asyncio
async def test_battle_context_apply_healing(
    battle_context: BattleContext,
    mock_actor: Stats,
    mock_target: Stats,
) -> None:
    """Test that BattleContext.apply_healing works correctly."""
    # Damage the target first
    mock_target.hp = 50

    healing_amount = 20.0
    healed = await battle_context.apply_healing(
        mock_actor,
        mock_target,
        healing_amount,
    )

    assert healed == 20
    assert mock_target.hp == 70


@pytest.mark.asyncio
async def test_battle_context_apply_healing_capped_at_max(
    battle_context: BattleContext,
    mock_actor: Stats,
    mock_target: Stats,
) -> None:
    """Test that healing is capped at max HP by default."""
    mock_target.hp = 75
    mock_target.max_hp = 80

    healing_amount = 20.0
    healed = await battle_context.apply_healing(
        mock_actor,
        mock_target,
        healing_amount,
    )

    # Should only heal 5 to reach max_hp
    assert healed == 5
    assert mock_target.hp == 80


@pytest.mark.asyncio
async def test_battle_context_apply_healing_overheal(
    battle_context: BattleContext,
    mock_actor: Stats,
    mock_target: Stats,
) -> None:
    """Test that overheal works when allowed."""
    mock_target.hp = 75
    mock_target.max_hp = 80

    healing_amount = 20.0
    healed = await battle_context.apply_healing(
        mock_actor,
        mock_target,
        healing_amount,
        overheal_allowed=True,
    )

    assert healed == 20
    assert mock_target.hp == 95


def test_battle_context_spend_resource_ultimate_charge(
    battle_context: BattleContext,
    mock_actor: Stats,
) -> None:
    """Test spending ultimate charge resource."""
    mock_actor.ultimate_charge = 100

    battle_context.spend_resource(mock_actor, "ultimate_charge", 50)

    assert mock_actor.ultimate_charge == 50


def test_battle_context_spend_resource_action_points(
    battle_context: BattleContext,
    mock_actor: Stats,
) -> None:
    """Test spending action points resource."""
    mock_actor.action_points = 3

    battle_context.spend_resource(mock_actor, "action_points", 1)

    assert mock_actor.action_points == 2


def test_battle_context_allies_of(
    battle_context: BattleContext,
    mock_actor: Stats,
) -> None:
    """Test that allies_of returns correct list."""
    allies = battle_context.allies_of(mock_actor)

    assert mock_actor in allies
    assert len(allies) == 1


def test_battle_context_enemies_of(
    battle_context: BattleContext,
    mock_actor: Stats,
    mock_target: Stats,
) -> None:
    """Test that enemies_of returns correct list."""
    enemies = battle_context.enemies_of(mock_actor)

    assert mock_target in enemies
    assert len(enemies) == 1


def test_battle_context_effect_manager_for(
    battle_context: BattleContext,
    mock_target: Stats,
) -> None:
    """Test that effect_manager_for creates or retrieves managers."""
    manager1 = battle_context.effect_manager_for(mock_target)

    assert isinstance(manager1, EffectManager)

    # Second call should return cached manager
    manager2 = battle_context.effect_manager_for(mock_target)
    assert manager1 is manager2
