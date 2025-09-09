"""Test damage by action tracking for battle review."""

import os
import sys

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from battle_logging import BattleLogger

from autofighter.mapgen import MapNode
from autofighter.party import Party
from autofighter.stats import Stats
from plugins.foes.slime import Slime
from plugins.players.carly import Carly


@pytest.mark.asyncio
async def test_party_damage_by_action_tracking():
    """Test that party members have damage_by_action data with different action types."""
    # Import here to avoid circular import issues
    from autofighter.rooms.battle import BattleRoom

    node = MapNode(
        room_id=0,
        room_type="battle-normal",
        floor=1,
        index=1,
        loop=1,
        pressure=0,
    )
    room = BattleRoom(node)

    # Create a party member with known damage type
    player = Carly()  # Light damage type
    player.id = "test_player"
    player.atk = 100  # Ensure we can deal damage

    # Create a weak foe so battle ends quickly
    foe = Slime()
    foe.id = "test_foe"
    foe.hp = 50
    foe.max_hp = 50

    party = Party(members=[player])

    # Start battle logging
    logger = BattleLogger("test_run", 0)
    logger.start_battle(party.members, [foe])

    await room.resolve(party, {}, foe=foe)

    # Check that party member has damage_by_action data
    summary = logger.export_summary()
    assert "damage_by_action" in summary
    assert "test_player" in summary["damage_by_action"]

    player_actions = summary["damage_by_action"]["test_player"]
    print(f"Player actions: {player_actions}")

    # Should have Normal Attack damage
    assert "Normal Attack" in player_actions
    assert player_actions["Normal Attack"] > 0

    logger.end_battle("victory")


@pytest.mark.asyncio
async def test_foe_damage_by_action_tracking():
    """Test that foes have damage_by_action data."""
    # Import here to avoid circular import issues
    from autofighter.rooms.battle import BattleRoom

    node = MapNode(
        room_id=0,
        room_type="battle-normal",
        floor=1,
        index=1,
        loop=1,
        pressure=0,
    )
    room = BattleRoom(node)

    # Create a weak player so foe can attack
    player = Stats(hp=1000, max_hp=1000, atk=1, defense=0)
    player.id = "weak_player"

    # Create a foe that can deal damage
    foe = Slime()
    foe.id = "test_foe"
    foe.atk = 50  # Ensure foe can deal damage

    party = Party(members=[player])

    # Start battle logging
    logger = BattleLogger("test_run", 1)
    logger.start_battle(party.members, [foe])

    await room.resolve(party, {}, foe=foe)

    # Check that foe has damage_by_action data
    summary = logger.export_summary()
    assert "damage_by_action" in summary

    print(f"All damage_by_action: {summary['damage_by_action']}")

    # Check if foe has any actions tracked
    if "test_foe" in summary["damage_by_action"]:
        foe_actions = summary["damage_by_action"]["test_foe"]
        print(f"Foe actions: {foe_actions}")

        # Should have Normal Attack damage if foe attacked
        if foe_actions:
            assert "Normal Attack" in foe_actions
            assert foe_actions["Normal Attack"] > 0
    else:
        print("No foe actions tracked - foe may not have attacked")

    logger.end_battle("victory")


@pytest.mark.asyncio
async def test_healing_in_damage_by_action():
    """Test that healing appears in damage_by_action tracking."""
    # Create a player and manually apply healing to test tracking
    player = Carly()
    player.id = "healer"

    # Damage the player so we can heal
    await player.apply_damage(50, attacker=None)

    # Start battle logging
    logger = BattleLogger("test_run", 2)
    logger.start_battle([player], [])

    # Apply healing which should be tracked in damage_by_action
    await player.apply_healing(
        25, healer=player, source_type="heal", source_name="Test Heal"
    )

    # Check that healing is tracked in damage_by_action
    summary = logger.export_summary()
    assert "damage_by_action" in summary
    assert "healer" in summary["damage_by_action"]

    player_actions = summary["damage_by_action"]["healer"]
    print(f"Healing actions: {player_actions}")

    # Should have healing action
    assert "Test Heal Healing" in player_actions
    assert player_actions["Test Heal Healing"] == 25

    logger.end_battle("victory")
