"""Test that active_effects are properly serialized for the frontend."""

from autofighter.effects import create_stat_buff
from autofighter.rooms.utils import _serialize
from plugins.characters._base import PlayerBase
from plugins.damage_types.generic import Generic


def test_active_effects_serialization():
    """Verify that active_effects are included in serialized Stats objects."""
    # Create a PlayerBase object
    player = PlayerBase(damage_type=Generic())
    player.id = "test_player"
    player.name = "Test Player"

    # Add a buff that creates an active effect
    buff = create_stat_buff(player, name='test_buff', atk=20, spd_mult=1.2)

    # Serialize the player
    serialized = _serialize(player)

    # Verify active_effects is in the serialized data
    assert 'active_effects' in serialized, "Serialized data should include active_effects field"

    # Verify active_effects is a list
    assert isinstance(serialized['active_effects'], list), "active_effects should be a list"

    # Verify we have at least one effect (the buff we just added)
    assert len(serialized['active_effects']) > 0, "Should have at least one active effect"

    # Verify the structure of the first effect
    effect = serialized['active_effects'][0]
    assert 'name' in effect, "Effect should have a name"
    assert 'source' in effect, "Effect should have a source"
    assert 'duration' in effect, "Effect should have a duration"
    assert 'modifiers' in effect, "Effect should have modifiers"
    assert 'description' in effect, "Effect should have a description"

    print("✓ active_effects serialization test passed")
    print(f"  - Found {len(serialized['active_effects'])} active effect(s)")
    print(f"  - Effect structure: {list(effect.keys())}")

    # Cleanup
    buff.remove()


def test_active_effects_empty_when_no_effects():
    """Verify that active_effects is an empty list when there are no effects."""
    player = PlayerBase(damage_type=Generic())
    player.id = "test_player_2"
    player.name = "Test Player 2"

    serialized = _serialize(player)

    # Should still have active_effects field, but empty
    assert 'active_effects' in serialized, "Serialized data should include active_effects field even when empty"
    assert isinstance(serialized['active_effects'], list), "active_effects should be a list"
    assert len(serialized['active_effects']) == 0, "Should have no active effects"

    print("✓ Empty active_effects test passed")


if __name__ == '__main__':
    test_active_effects_serialization()
    test_active_effects_empty_when_no_effects()
    print("\nAll serialization tests passed!")
