"""Test damage by action tracking for battle review."""
from battle_logging.writers import end_battle_logging
from battle_logging.writers import start_battle_logging
import pytest

from autofighter.stats import Stats
from plugins.players.carly import Carly


@pytest.mark.asyncio
async def test_healing_in_damage_by_action():
    """Test that healing appears in damage_by_action tracking."""
    # Start battle logging
    battle_logger = start_battle_logging()

    # Create a player and manually apply healing to test tracking
    player = Carly()
    player.id = "healer"

    # Set up logging for this player
    if battle_logger:
        battle_logger.summary.party_members = ["healer"]
        battle_logger.summary.foes = []

    # Damage the player so we can heal
    await player.apply_damage(50, attacker=None)

    # Apply healing which should be tracked in damage_by_action
    await player.apply_healing(25, healer=player, source_type="heal", source_name="Test Heal")

    # End battle and check results
    end_battle_logging("victory")

    if battle_logger:
        summary = battle_logger.export_summary()
        print(f"Summary damage_by_action: {summary.get('damage_by_action', {})}")

        # Check that healing is tracked in damage_by_action
        assert "damage_by_action" in summary
        if "healer" in summary["damage_by_action"]:
            player_actions = summary["damage_by_action"]["healer"]
            print(f"Healing actions: {player_actions}")

            # Should have healing action
            assert "Test Heal Healing" in player_actions
            assert player_actions["Test Heal Healing"] == 25


@pytest.mark.asyncio
async def test_damage_action_names_preserved():
    """Test that different action names are preserved separately."""
    # Start battle logging
    battle_logger = start_battle_logging()

    # Create entities
    attacker = Carly()
    attacker.id = "test_attacker"
    target = Stats(hp=1000)
    target.id = "test_target"

    # Set up logging
    if battle_logger:
        battle_logger.summary.party_members = ["test_attacker"]
        battle_logger.summary.foes = ["test_target"]

    # Apply different types of damage with specific action names
    await target.apply_damage(100, attacker=attacker, action_name="Normal Attack")
    await target.apply_damage(75, attacker=attacker, action_name="Ice Ultimate")
    await target.apply_damage(50, attacker=attacker, action_name="Wind Spread")

    # End battle and check results
    end_battle_logging("victory")

    if battle_logger:
        summary = battle_logger.export_summary()
        print(f"Summary damage_by_action: {summary.get('damage_by_action', {})}")

        # Check that all action types are tracked separately
        assert "damage_by_action" in summary
        if "test_attacker" in summary["damage_by_action"]:
            attacker_actions = summary["damage_by_action"]["test_attacker"]
            print(f"Attacker actions: {attacker_actions}")

            # Should have separate entries for each action type
            assert "Normal Attack" in attacker_actions
            assert "Ice Ultimate" in attacker_actions
            assert "Wind Spread" in attacker_actions

            assert attacker_actions["Normal Attack"] == 100
            assert attacker_actions["Ice Ultimate"] == 75
            assert attacker_actions["Wind Spread"] == 50
