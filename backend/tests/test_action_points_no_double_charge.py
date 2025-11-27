"""Test that action points are not double-charged when using action plugin system."""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from autofighter.effects import EffectManager
from autofighter.passives import PassiveRegistry
from autofighter.rooms.battle.turn_loop.initialization import initialize_turn_loop
from autofighter.stats import Stats


@pytest.fixture
def mock_party():
    """Create a mock party with one member that has multiple action points."""
    party = Mock()
    member = Stats()
    member.id = "test_member"
    member.hp = 100
    member.max_hp = 100
    member.atk = 10
    member.actions_per_turn = 3  # Character with multiple actions per turn
    member.action_points = 3
    member.damage_type = Mock(id="generic")
    party.members = [member]
    return party


@pytest.fixture
def mock_foes():
    """Create mock foes with multiple action points."""
    foe = Stats()
    foe.id = "test_foe"
    foe.hp = 50
    foe.max_hp = 50
    foe.atk = 5
    foe.actions_per_turn = 2  # Foe with multiple actions
    foe.action_points = 2
    foe.damage_type = Mock(id="generic")
    return [foe]


@pytest.fixture
def mock_battle_room():
    """Create a mock battle room."""
    room = Mock()
    room.id = "test_battle"
    return room


@pytest.fixture
def mock_enrage_state():
    """Create a mock enrage state."""
    enrage_state = Mock()
    enrage_state.max_turns = 10
    enrage_state.turn = 0
    enrage_state.active = False
    return enrage_state


@pytest.mark.asyncio
async def test_player_action_points_not_double_charged(
    mock_battle_room,
    mock_party,
    mock_foes,
    mock_enrage_state,
):
    """Test that player action points are only deducted once when using action plugins."""
    registry = PassiveRegistry()
    foe_effects = [EffectManager(foe) for foe in mock_foes]

    context = await initialize_turn_loop(
        room=mock_battle_room,
        party=mock_party,
        combat_party=mock_party,
        registry=registry,
        foes=mock_foes,
        foe_effects=foe_effects,
        enrage_mods=[],
        enrage_state=mock_enrage_state,
        progress=None,
        visual_queue=None,
        temp_rdr=1.0,
        exp_reward=100,
        run_id="test_run",
        battle_tasks={},
        abort=lambda msg: None,
    )

    member = mock_party.members[0]
    foe = mock_foes[0]
    initial_action_points = member.action_points

    # Verify member starts with 3 action points
    assert initial_action_points == 3

    # Create BattleContext
    from autofighter.rooms.battle.turn_loop.initialization import create_battle_context

    battle_context = create_battle_context(
        context,
        phase="player",
        actor=member,
        allies=list(mock_party.members),
        enemies=list(mock_foes),
    )

    # Execute basic attack action
    action = context.action_registry.instantiate("normal.basic_attack")
    await action.run(member, [foe], battle_context)

    # Verify action points were deducted exactly once (3 - 1 = 2)
    assert member.action_points == 2, (
        f"Expected 2 action points after one attack, but got {member.action_points}. "
        "Action points may have been double-charged."
    )


@pytest.mark.asyncio
async def test_foe_action_points_not_double_charged(
    mock_battle_room,
    mock_party,
    mock_foes,
    mock_enrage_state,
):
    """Test that foe action points are only deducted once when using action plugins."""
    registry = PassiveRegistry()
    foe_effects = [EffectManager(foe) for foe in mock_foes]

    context = await initialize_turn_loop(
        room=mock_battle_room,
        party=mock_party,
        combat_party=mock_party,
        registry=registry,
        foes=mock_foes,
        foe_effects=foe_effects,
        enrage_mods=[],
        enrage_state=mock_enrage_state,
        progress=None,
        visual_queue=None,
        temp_rdr=1.0,
        exp_reward=100,
        run_id="test_run",
        battle_tasks={},
        abort=lambda msg: None,
    )

    member = mock_party.members[0]
    foe = mock_foes[0]
    initial_action_points = foe.action_points

    # Verify foe starts with 2 action points
    assert initial_action_points == 2

    # Create BattleContext for foe phase
    from autofighter.rooms.battle.turn_loop.initialization import create_battle_context

    battle_context = create_battle_context(
        context,
        phase="foe",
        actor=foe,
        allies=list(mock_foes),
        enemies=list(mock_party.members),
    )

    # Execute basic attack action
    action = context.action_registry.instantiate("normal.basic_attack")
    await action.run(foe, [member], battle_context)

    # Verify action points were deducted exactly once (2 - 1 = 1)
    assert foe.action_points == 1, (
        f"Expected 1 action point after one attack, but got {foe.action_points}. "
        "Action points may have been double-charged."
    )


@pytest.mark.asyncio
async def test_multiple_actions_with_action_registry(
    mock_battle_room,
    mock_party,
    mock_foes,
    mock_enrage_state,
):
    """Test that characters with multiple actions can use them all without double-charging."""
    registry = PassiveRegistry()
    foe_effects = [EffectManager(foe) for foe in mock_foes]

    context = await initialize_turn_loop(
        room=mock_battle_room,
        party=mock_party,
        combat_party=mock_party,
        registry=registry,
        foes=mock_foes,
        foe_effects=foe_effects,
        enrage_mods=[],
        enrage_state=mock_enrage_state,
        progress=None,
        visual_queue=None,
        temp_rdr=1.0,
        exp_reward=100,
        run_id="test_run",
        battle_tasks={},
        abort=lambda msg: None,
    )

    member = mock_party.members[0]
    foe = mock_foes[0]

    # Member starts with 3 action points
    assert member.action_points == 3

    # Create BattleContext
    from autofighter.rooms.battle.turn_loop.initialization import create_battle_context

    battle_context = create_battle_context(
        context,
        phase="player",
        actor=member,
        allies=list(mock_party.members),
        enemies=list(mock_foes),
    )

    # Execute first attack
    action = context.action_registry.instantiate("normal.basic_attack")
    await action.run(member, [foe], battle_context)
    assert member.action_points == 2

    # Execute second attack
    await action.run(member, [foe], battle_context)
    assert member.action_points == 1

    # Execute third attack
    await action.run(member, [foe], battle_context)
    assert member.action_points == 0

    # Verify character used all 3 actions as expected
