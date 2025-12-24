"""Comprehensive tests for the combat engine.

Tests action queue, battle initialization, turn execution, damage calculation,
and reward generation.
"""

import pytest

from core.action_queue import ActionQueue
from core.action_queue import TURN_COUNTER_ID
from core.battle.engine import BattleResult
from core.battle.engine import finalize_battle
from core.battle.engine import run_battle
from core.battle.engine import run_battle_step
from core.battle.events import handle_battle_end
from core.battle.events import handle_battle_start
from core.battle.events import handle_damage_dealt
from core.battle.foe_turn import execute_foe_turn
from core.battle.initialization import EnrageState
from core.battle.initialization import TurnLoopContext
from core.battle.initialization import initialize_turn_loop
from core.battle.player_turn import execute_player_turn
from core.battle.resolution import calculate_battle_rewards
from core.stats import GAUGE_START
from core.stats import Stats


# Fixtures


@pytest.fixture
def basic_party_member():
    """Create a basic party member for testing."""
    stats = Stats()
    stats.id = "hero_1"
    stats.hp = 1000
    stats._base_max_hp = 1000
    stats._base_atk = 200
    stats._base_defense = 100
    stats._base_spd = 10
    stats.level = 5
    stats.actions_per_turn = 1
    stats.action_points = 1
    return stats


@pytest.fixture
def basic_foe():
    """Create a basic foe for testing."""
    stats = Stats()
    stats.id = "goblin_1"
    stats.hp = 500
    stats._base_max_hp = 500
    stats._base_atk = 150
    stats._base_defense = 50
    stats._base_spd = 8
    stats.level = 3
    stats.actions_per_turn = 1
    stats.action_points = 1
    return stats


@pytest.fixture
def party():
    """Create a party with 3 members."""
    members = []
    for i in range(3):
        stats = Stats()
        stats.id = f"hero_{i}"
        stats.hp = 1000
        stats._base_max_hp = 1000
        stats._base_atk = 200
        stats._base_defense = 100
        stats._base_spd = 10 + i  # Varying speeds
        stats.level = 5
        stats.actions_per_turn = 1
        stats.action_points = 1
        members.append(stats)
    return members


@pytest.fixture
def foes():
    """Create a group of 2 foes."""
    enemies = []
    for i in range(2):
        stats = Stats()
        stats.id = f"goblin_{i}"
        stats.hp = 500
        stats._base_max_hp = 500
        stats._base_atk = 150
        stats._base_defense = 50
        stats._base_spd = 8 + i
        stats.level = 3
        stats.actions_per_turn = 1
        stats.action_points = 1
        enemies.append(stats)
    return enemies


# Action Queue Tests


def test_action_queue_initialization():
    """Test action queue initializes correctly."""
    stats1 = Stats()
    stats1.id = "actor1"
    stats1._base_spd = 10

    stats2 = Stats()
    stats2.id = "actor2"
    stats2._base_spd = 20

    queue = ActionQueue(combatants=[stats1, stats2])

    # Check gauges initialized (should be set to base_action_value)
    # For SPD=10: base_action_value = 10000/10 = 1000
    # For SPD=20: base_action_value = 10000/20 = 500
    assert stats1.action_gauge == 1000.0
    assert stats2.action_gauge == 500.0

    # Faster character should have lower action value
    assert stats2.action_value < stats1.action_value


def test_action_queue_turn_order():
    """Test action queue returns actors in correct speed order."""
    slow = Stats()
    slow.id = "slow"
    slow._base_spd = 5

    fast = Stats()
    fast.id = "fast"
    fast._base_spd = 15

    queue = ActionQueue(combatants=[slow, fast])

    # Fast actor should go first
    first = queue.next_actor()
    assert first.id == "fast"


def test_action_queue_extra_turn():
    """Test extra turn functionality."""
    actor1 = Stats()
    actor1.id = "actor1"
    actor1._base_spd = 10

    actor2 = Stats()
    actor2.id = "actor2"
    actor2._base_spd = 10

    queue = ActionQueue(combatants=[actor1, actor2])

    # Grant extra turn to actor2
    queue.grant_extra_turn(actor2)

    # Actor2 should go next regardless of queue
    next_actor = queue.next_actor()
    assert next_actor.id == "actor2"


def test_action_queue_snapshot():
    """Test action queue snapshot generation."""
    actor = Stats()
    actor.id = "test_actor"
    actor._base_spd = 10

    queue = ActionQueue(combatants=[actor])
    snapshot = queue.snapshot()

    assert len(snapshot) > 0
    assert snapshot[0]["id"] == "test_actor"
    assert "action_gauge" in snapshot[0]
    assert "action_value" in snapshot[0]


# Battle Initialization Tests


def test_enrage_state():
    """Test enrage state tracking."""
    enrage = EnrageState(threshold=10)

    assert not enrage.is_enraged()
    assert enrage.get_percent() == 0.0

    enrage.increment(5)
    assert not enrage.is_enraged()
    assert enrage.get_percent() == 0.5

    enrage.increment(5)
    assert enrage.is_enraged()
    assert enrage.get_percent() == 1.0


def test_turn_loop_context_creation(party, foes):
    """Test turn loop context initialization."""
    context = initialize_turn_loop(
        party_members=party,
        foes=foes,
        enrage_threshold=50,
    )

    assert len(context.party_members) == 3
    assert len(context.foes) == 2
    assert context.turn == 0
    assert context.action_queue is not None
    assert not context.is_battle_over()


def test_battle_victory_detection(party, foes):
    """Test victory detection."""
    context = initialize_turn_loop(party_members=party, foes=foes)

    # Kill all foes
    for foe in context.foes:
        foe.hp = 0

    assert context.is_battle_over()
    assert context.is_victory()
    assert not context.is_defeat()


def test_battle_defeat_detection(party, foes):
    """Test defeat detection."""
    context = initialize_turn_loop(party_members=party, foes=foes)

    # Kill all party members
    for member in context.party_members:
        member.hp = 0

    assert context.is_battle_over()
    assert not context.is_victory()
    assert context.is_defeat()


# Turn Execution Tests


def test_player_turn_execution(party, foes):
    """Test player turn executes and deals damage."""
    context = initialize_turn_loop(party_members=party, foes=foes)
    actor = party[0]

    initial_foe_hp = foes[0].hp

    # Execute player turn
    continue_battle = execute_player_turn(context, actor)

    # Should continue and foe should take damage
    assert continue_battle
    assert foes[0].hp < initial_foe_hp or foes[1].hp < 500


def test_foe_turn_execution(party, foes):
    """Test foe turn executes and deals damage."""
    context = initialize_turn_loop(party_members=party, foes=foes)
    actor = foes[0]

    initial_party_hp = sum(m.hp for m in party)

    # Execute foe turn
    continue_battle = execute_foe_turn(context, actor)

    # Should continue and party should take damage
    assert continue_battle
    current_party_hp = sum(m.hp for m in party)
    assert current_party_hp <= initial_party_hp


def test_player_turn_with_dead_actor(party, foes):
    """Test player turn with dead actor doesn't crash."""
    context = initialize_turn_loop(party_members=party, foes=foes)
    actor = party[0]
    actor.hp = 0

    # Should handle gracefully
    continue_battle = execute_player_turn(context, actor)
    assert continue_battle or context.is_battle_over()


def test_damage_tracking():
    """Test damage tracking in stats."""
    attacker = Stats()
    attacker.id = "attacker"
    attacker._base_atk = 200

    target = Stats()
    target.id = "target"
    target.hp = 1000

    initial_hp = target.hp

    # Simulate damage event
    handle_damage_dealt(attacker, target, 100, "Generic")

    # Check tracking updated
    assert attacker.damage_dealt_total >= 100
    assert target.damage_taken_total >= 100
    assert target.last_damage_taken >= 100


# Combat Mechanics Tests


def test_shield_absorption():
    """Test shields absorb damage correctly."""
    target = Stats()
    target.hp = 1000
    target.shields = 200

    # Import damage application function
    from core.battle.player_turn import _apply_damage

    # Damage less than shields
    actual = _apply_damage(target, 100)
    assert target.shields == 100
    assert target.hp == 1000
    assert actual == 0

    # Damage exceeds shields
    actual = _apply_damage(target, 150)
    assert target.shields == 0
    assert target.hp == 950
    assert actual == 50


def test_dodge_mechanic():
    """Test dodge can avoid damage."""
    target = Stats()
    target.hp = 1000
    target._base_dodge_odds = 1.0  # 100% dodge for testing

    from core.battle.player_turn import _apply_damage

    actual = _apply_damage(target, 500)
    assert actual == 0
    assert target.hp == 1000


# Battle Engine Tests


def test_run_battle_victory(party, foes):
    """Test full battle execution resulting in victory."""
    # Make party much stronger
    for member in party:
        member._base_atk = 1000

    result = run_battle(party_members=party, foes=foes, max_turns=100)

    assert isinstance(result, BattleResult)
    assert result.victory
    assert result.turns_taken > 0
    assert result.gold > 0
    assert result.exp > 0
    assert len(result.party_survivors) == 3


def test_run_battle_defeat(party, foes):
    """Test full battle execution resulting in defeat."""
    # Make foes much stronger and more numerous
    for foe in foes:
        foe._base_atk = 5000  # Much higher ATK
        foe._base_max_hp = 5000
        foe.hp = 5000

    # Add more foes
    extra_foe = Stats()
    extra_foe.id = "goblin_boss"
    extra_foe._base_atk = 5000
    extra_foe._base_max_hp = 5000
    extra_foe.hp = 5000
    extra_foe._base_spd = 12
    foes.append(extra_foe)

    result = run_battle(party_members=party, foes=foes, max_turns=100)

    assert isinstance(result, BattleResult)
    assert not result.victory
    assert result.gold == 0
    assert result.exp == 0


def test_run_battle_step(party, foes):
    """Test incremental battle step execution."""
    context = initialize_turn_loop(party_members=party, foes=foes)

    steps = 0
    max_steps = 200

    while steps < max_steps:
        continues, won = run_battle_step(context)
        steps += 1

        if not continues:
            break

    # Battle should end eventually
    assert steps < max_steps
    assert context.is_battle_over()


def test_finalize_battle(party, foes):
    """Test battle finalization and rewards."""
    context = initialize_turn_loop(party_members=party, foes=foes)

    # Simulate victory
    for foe in context.foes:
        foe.hp = 0

    result = finalize_battle(context)

    assert result.victory
    assert result.gold > 0
    assert result.exp > 0


# Event System Tests


def test_battle_start_event(party, foes):
    """Test battle start event handler."""
    # Should not crash
    handle_battle_start(foes, party)

    # Action points should be initialized
    for member in party:
        assert hasattr(member, "action_points")
    for foe in foes:
        assert hasattr(foe, "action_points")


def test_battle_end_event(party, foes):
    """Test battle end event handler."""
    # Kill a foe
    foes[0].hp = 0

    # Should not crash
    handle_battle_end(foes, party)


# Reward System Tests


def test_calculate_battle_rewards_victory():
    """Test reward calculation for victory."""
    context = initialize_turn_loop(party_members=[Stats()], foes=[Stats()])
    context.turn = 10

    rewards = calculate_battle_rewards(context, victory=True, temp_rdr=1.0)

    assert rewards["victory"]
    assert rewards["gold"] > 0
    assert rewards["exp"] > 0
    assert isinstance(rewards["cards"], list)
    assert isinstance(rewards["relics"], list)
    assert isinstance(rewards["items"], list)


def test_calculate_battle_rewards_defeat():
    """Test reward calculation for defeat."""
    context = initialize_turn_loop(party_members=[Stats()], foes=[Stats()])

    rewards = calculate_battle_rewards(context, victory=False)

    assert not rewards["victory"]
    assert rewards["gold"] == 0
    assert rewards["exp"] == 0
    assert len(rewards["cards"]) == 0


def test_rdr_multiplier_affects_rewards():
    """Test that RDR multiplier increases rewards."""
    context = initialize_turn_loop(party_members=[Stats()], foes=[Stats()])

    normal_rewards = calculate_battle_rewards(context, victory=True, temp_rdr=1.0)
    boosted_rewards = calculate_battle_rewards(context, victory=True, temp_rdr=5.0)

    # Gold should be higher with RDR boost
    assert boosted_rewards["gold"] > normal_rewards["gold"]


# Edge Cases


def test_empty_battle():
    """Test battle with no combatants doesn't crash."""
    # Should handle gracefully
    result = run_battle(party_members=[], foes=[], max_turns=10)
    assert isinstance(result, BattleResult)


def test_max_turns_limit():
    """Test battle respects max turns limit."""
    # Create evenly matched combatants
    party = [Stats() for _ in range(2)]
    foes = [Stats() for _ in range(2)]

    for member in party:
        member.hp = 10000
        member._base_defense = 500

    for foe in foes:
        foe.hp = 10000
        foe._base_defense = 500

    result = run_battle(party_members=party, foes=foes, max_turns=10)

    # Should stop at max turns
    assert result.turns_taken <= 10


def test_action_points_reset():
    """Test action points reset correctly between turns."""
    actor = Stats()
    actor.id = "test"
    actor.actions_per_turn = 2
    actor.action_points = 0

    context = initialize_turn_loop(party_members=[actor], foes=[Stats()])

    execute_player_turn(context, actor)

    # Action points should reset
    assert actor.action_points >= 1
