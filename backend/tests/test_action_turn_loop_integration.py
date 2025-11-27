"""Integration tests for action plugin execution in turn loop."""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from autofighter.effects import EffectManager
from autofighter.passives import PassiveRegistry
from autofighter.rooms.battle.turn_loop.initialization import create_battle_context
from autofighter.rooms.battle.turn_loop.initialization import initialize_turn_loop
from autofighter.stats import Stats
from plugins.actions.registry import ActionRegistry


@pytest.fixture
def mock_party():
    """Create a mock party with one member."""
    party = Mock()
    member = Stats()
    member.id = "test_member"
    member.hp = 100
    member.max_hp = 100
    member.atk = 10
    member.actions_per_turn = 1
    member.action_points = 1
    member.damage_type = Mock(id="generic")
    party.members = [member]
    return party


@pytest.fixture
def mock_foes():
    """Create mock foes."""
    foe = Stats()
    foe.id = "test_foe"
    foe.hp = 50
    foe.max_hp = 50
    foe.atk = 5
    foe.actions_per_turn = 1
    foe.action_points = 1
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
async def test_initialize_turn_loop_creates_action_registry(
    mock_battle_room,
    mock_party,
    mock_foes,
    mock_enrage_state,
):
    """Test that initialize_turn_loop creates and populates ActionRegistry."""
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

    # Verify ActionRegistry was created
    assert context.action_registry is not None
    assert isinstance(context.action_registry, ActionRegistry)

    # Verify BasicAttackAction was registered
    basic_attack = context.action_registry.instantiate("normal.basic_attack")
    assert basic_attack is not None
    assert basic_attack.id == "normal.basic_attack"
    assert basic_attack.name == "Basic Attack"


@pytest.mark.asyncio
async def test_create_battle_context_from_turn_loop_context(
    mock_battle_room,
    mock_party,
    mock_foes,
    mock_enrage_state,
):
    """Test that create_battle_context properly builds BattleContext."""
    registry = PassiveRegistry()
    foe_effects = [EffectManager(foe) for foe in mock_foes]

    turn_context = await initialize_turn_loop(
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

    # Create BattleContext for player phase
    battle_context = create_battle_context(
        turn_context,
        phase="player",
        actor=member,
        allies=list(mock_party.members),
        enemies=list(mock_foes),
    )

    # Verify BattleContext fields
    assert battle_context.turn == 0
    assert battle_context.run_id == "test_run"
    assert battle_context.phase == "player"
    assert battle_context.actor is member
    assert list(battle_context.allies) == [member]
    assert list(battle_context.enemies) == [foe]
    assert battle_context.action_registry is not None
    assert battle_context.passive_registry is registry
    assert battle_context.event_bus is not None


@pytest.mark.asyncio
async def test_action_plugin_executes_in_player_turn_context(
    mock_battle_room,
    mock_party,
    mock_foes,
    mock_enrage_state,
):
    """Test that action plugin can execute successfully in player turn context."""
    registry = PassiveRegistry()
    foe_effects = [EffectManager(foe) for foe in mock_foes]

    turn_context = await initialize_turn_loop(
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

    # Create BattleContext
    battle_context = create_battle_context(
        turn_context,
        phase="player",
        actor=member,
        allies=list(mock_party.members),
        enemies=list(mock_foes),
    )

    # Execute basic attack action
    action = turn_context.action_registry.instantiate("normal.basic_attack")
    result = await action.run(member, [foe], battle_context)

    # Verify action executed successfully
    assert result.success is True
    assert len(result.damage_dealt) > 0

    # Verify damage was applied to foe
    target_id = str(getattr(foe, "id", id(foe)))
    assert target_id in result.damage_dealt
    damage = result.damage_dealt[target_id]
    assert damage >= 0  # Could be 0 if dodged
    assert foe.hp <= 50  # HP should be reduced (or stay same if dodged)


@pytest.mark.asyncio
async def test_action_plugin_executes_in_foe_turn_context(
    mock_battle_room,
    mock_party,
    mock_foes,
    mock_enrage_state,
):
    """Test that action plugin can execute successfully in foe turn context."""
    registry = PassiveRegistry()
    foe_effects = [EffectManager(foe) for foe in mock_foes]

    turn_context = await initialize_turn_loop(
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

    # Create BattleContext for foe phase
    battle_context = create_battle_context(
        turn_context,
        phase="foe",
        actor=foe,
        allies=list(mock_foes),
        enemies=list(mock_party.members),
    )

    # Execute basic attack action
    action = turn_context.action_registry.instantiate("normal.basic_attack")
    result = await action.run(foe, [member], battle_context)

    # Verify action executed successfully
    assert result.success is True
    assert len(result.damage_dealt) > 0

    # Verify damage was applied to member
    target_id = str(getattr(member, "id", id(member)))
    assert target_id in result.damage_dealt
    damage = result.damage_dealt[target_id]
    assert damage >= 0  # Could be 0 if dodged
    assert member.hp <= 100  # HP should be reduced (or stay same if dodged)


@pytest.mark.asyncio
async def test_action_cost_deduction(
    mock_battle_room,
    mock_party,
    mock_foes,
    mock_enrage_state,
):
    """Test that action cost (action points) is properly deducted."""
    registry = PassiveRegistry()
    foe_effects = [EffectManager(foe) for foe in mock_foes]

    turn_context = await initialize_turn_loop(
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

    # Create BattleContext
    battle_context = create_battle_context(
        turn_context,
        phase="player",
        actor=member,
        allies=list(mock_party.members),
        enemies=list(mock_foes),
    )

    # Execute basic attack action
    action = turn_context.action_registry.instantiate("normal.basic_attack")
    await action.run(member, [foe], battle_context)

    # Verify action points were deducted
    assert member.action_points == initial_action_points - 1
