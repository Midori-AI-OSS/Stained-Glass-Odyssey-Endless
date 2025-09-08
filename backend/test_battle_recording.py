"""
Test the turn-based battle recording system.
"""
import pytest
import asyncio
from datetime import datetime
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from battle_recording import (
    TurnAction,
    BattleRecording,
    start_battle_recording,
    get_battle_recording,
    end_battle_recording,
    clear_battle_recording,
    create_attack_action,
    create_heal_action,
    get_animation_for_damage_type,
    get_color_for_damage_type,
    wait_for_frontend_confirmation,
    battle_recordings
)


def test_turn_action_creation():
    """Test creating turn actions."""
    # Test attack action
    attack = create_attack_action(
        actor_id="player1",
        target_id="enemy1", 
        damage=50,
        damage_type="Fire",
        is_critical=True,
        action_name="Fireball"
    )
    
    assert attack.actor_id == "player1"
    assert attack.target_id == "enemy1"
    assert attack.amount == 50
    assert attack.damage_type == "Fire"
    assert attack.is_critical is True
    assert attack.action_name == "Fireball"
    assert attack.animation_name == "HitFire.efkefc"
    assert attack.effect_color == "#FF4444"
    
    # Test heal action
    heal = create_heal_action(
        actor_id="healer1",
        target_id="player1",
        healing=30,
        action_name="Cure"
    )
    
    assert heal.actor_id == "healer1"
    assert heal.target_id == "player1"
    assert heal.amount == 30
    assert heal.action_type == "heal"
    assert heal.animation_name == "HealOne1.efkefc"
    assert heal.effect_color == "#44FF44"


def test_damage_type_animations():
    """Test damage type to animation mapping."""
    assert get_animation_for_damage_type("Fire", "attack") == "HitFire.efkefc"
    assert get_animation_for_damage_type("Ice", "spell") == "Ice1.efkefc"
    assert get_animation_for_damage_type("Lightning", "breath") == "BreathThunder.efkefc"
    assert get_animation_for_damage_type("Water", "attack") == "HitPhysical.efkefc"
    assert get_animation_for_damage_type(None, "attack") == "HitPhysical.efkefc"


def test_damage_type_colors():
    """Test damage type to color mapping."""
    assert get_color_for_damage_type("Fire") == "#FF4444"
    assert get_color_for_damage_type("Ice") == "#44AAFF"
    assert get_color_for_damage_type("Lightning") == "#FFFF44"
    assert get_color_for_damage_type(None) == "#FFFFFF"


def test_battle_recording_lifecycle():
    """Test the full battle recording lifecycle."""
    run_id = "test_run_123"
    battle_id = "test_battle_1"
    
    # Start recording
    recording = start_battle_recording(run_id, battle_id)
    assert recording.run_id == run_id
    assert recording.battle_id == battle_id
    assert recording.is_complete is False
    assert recording.current_action_index == 0
    
    # Check it's stored correctly
    stored = get_battle_recording(run_id)
    assert stored is recording
    
    # Add some actions
    attack1 = create_attack_action("player1", "enemy1", 25, "Fire")
    attack2 = create_attack_action("enemy1", "player1", 15, "Ice")
    heal1 = create_heal_action("player1", "player1", 10)
    
    recording.add_action(attack1)
    recording.add_action(attack2)
    recording.add_action(heal1)
    
    assert len(recording.actions) == 3
    
    # Test getting next action
    next_action = recording.get_next_action()
    assert next_action is attack1
    assert recording.current_action_index == 0
    
    # Confirm action complete
    success = recording.confirm_action_complete()
    assert success is True
    assert recording.current_action_index == 1
    
    # Get next action
    next_action = recording.get_next_action()
    assert next_action is attack2
    
    # Confirm again
    recording.confirm_action_complete()
    assert recording.current_action_index == 2
    
    # Get final action
    next_action = recording.get_next_action()
    assert next_action is heal1
    
    # Confirm final action
    recording.confirm_action_complete()
    assert recording.current_action_index == 3
    
    # No more actions
    next_action = recording.get_next_action()
    assert next_action is None
    
    # End recording
    end_battle_recording(run_id, "victory")
    assert recording.is_complete is True
    assert recording.result == "victory"
    
    # Clean up
    clear_battle_recording(run_id)
    assert get_battle_recording(run_id) is None


@pytest.mark.asyncio
async def test_frontend_confirmation_timeout():
    """Test that frontend confirmation times out properly."""
    run_id = "test_timeout"
    battle_id = "test_battle_timeout"
    
    # Start recording
    recording = start_battle_recording(run_id, battle_id)
    attack = create_attack_action("player1", "enemy1", 25)
    recording.add_action(attack)
    
    # Mark as awaiting frontend
    recording.awaiting_frontend = True
    
    # Test timeout (use very short timeout for test)
    start_time = asyncio.get_event_loop().time()
    result = await wait_for_frontend_confirmation(run_id, timeout_seconds=0.2)
    elapsed = asyncio.get_event_loop().time() - start_time
    
    # Should timeout and auto-advance
    assert result is False
    assert elapsed >= 0.2
    assert recording.awaiting_frontend is False
    assert recording.current_action_index == 1
    
    # Clean up
    clear_battle_recording(run_id)


def test_action_serialization():
    """Test that actions can be serialized to dict/JSON."""
    attack = create_attack_action(
        actor_id="player1",
        target_id="enemy1",
        damage=50,
        damage_type="Fire",
        is_critical=True
    )
    
    serialized = attack.to_dict()
    
    assert isinstance(serialized, dict)
    assert serialized['actor_id'] == "player1"
    assert serialized['target_id'] == "enemy1"
    assert serialized['amount'] == 50
    assert serialized['damage_type'] == "Fire"
    assert serialized['is_critical'] is True
    assert serialized['animation_name'] == "HitFire.efkefc"
    assert serialized['effect_color'] == "#FF4444"
    
    # Test that timestamp is serializable
    assert isinstance(serialized['timestamp'], str)


def test_recording_serialization():
    """Test that battle recordings can be serialized."""
    run_id = "test_serialization"
    battle_id = "test_battle_serial"
    
    recording = start_battle_recording(run_id, battle_id)
    recording.party_members = ["player1", "ally1"]
    recording.foes = ["enemy1", "enemy2"]
    
    attack = create_attack_action("player1", "enemy1", 25)
    recording.add_action(attack)
    
    serialized = recording.to_dict()
    
    assert isinstance(serialized, dict)
    assert serialized['run_id'] == run_id
    assert serialized['battle_id'] == battle_id
    assert serialized['party_members'] == ["player1", "ally1"]
    assert serialized['foes'] == ["enemy1", "enemy2"]
    assert len(serialized['actions']) == 1
    assert isinstance(serialized['actions'][0], dict)
    
    # Clean up
    clear_battle_recording(run_id)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])