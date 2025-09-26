"""Test foe scaling with cumulative room progression across floors."""
from pathlib import Path
import random
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from autofighter.mapgen import MapGenerator
from autofighter.mapgen import MapNode
from autofighter.rooms.utils import _scale_stats
from plugins.characters.foe_base import FoeBase


def test_foe_scaling_cumulative_rooms():
    """Test that foe scaling uses cumulative room progression across floors."""
    # Create test foes with identical base stats
    foe1 = FoeBase()
    foe1.set_base_stat('atk', 100)
    foe1.set_base_stat('defense', 50)
    foe1.set_base_stat('max_hp', 1000)
    foe1.hp = 1000

    foe2 = FoeBase()
    foe2.set_base_stat('atk', 100)
    foe2.set_base_stat('defense', 50)
    foe2.set_base_stat('max_hp', 1000)
    foe2.hp = 1000

    # Room 1 Floor 1 (cumulative room 1)
    node1 = MapNode(room_id=1, room_type="battle-normal", floor=1, index=1, loop=1, pressure=0)

    # Room 1 Floor 2 (cumulative room 46: 45 + 1)
    node2 = MapNode(room_id=1, room_type="battle-normal", floor=2, index=1, loop=1, pressure=0)

    # Set random seed for reproducible results
    random.seed(42)
    _scale_stats(foe1, node1)

    # Reset random seed to same state for comparison
    random.seed(42)

    # Reset foe2 and test floor 2 room 1
    random.seed(42)
    _scale_stats(foe2, node2)

    # Foe2 should be significantly stronger than foe1 since it's equivalent to room 46
    assert foe2.atk > foe1.atk, f"Floor 2 Room 1 foe should be stronger than Floor 1 Room 1: {foe2.atk} > {foe1.atk}"
    assert foe2.max_hp > foe1.max_hp, f"Floor 2 Room 1 foe should have more HP than Floor 1 Room 1: {foe2.max_hp} > {foe1.max_hp}"


def test_foe_scaling_room_progression_within_floor():
    """Test that rooms within a floor still progress correctly."""
    foe1 = FoeBase()
    foe1.set_base_stat('atk', 100)
    foe1.set_base_stat('defense', 50)
    foe1.set_base_stat('max_hp', 1000)
    foe1.hp = 1000

    foe2 = FoeBase()
    foe2.set_base_stat('atk', 100)
    foe2.set_base_stat('defense', 50)
    foe2.set_base_stat('max_hp', 1000)
    foe2.hp = 1000

    # Room 5 Floor 1
    node1 = MapNode(room_id=5, room_type="battle-normal", floor=1, index=5, loop=1, pressure=0)

    # Room 10 Floor 1
    node2 = MapNode(room_id=10, room_type="battle-normal", floor=1, index=10, loop=1, pressure=0)

    random.seed(42)
    _scale_stats(foe1, node1)

    random.seed(42)
    _scale_stats(foe2, node2)

    # Room 10 should be stronger than room 5 within the same floor
    assert foe2.atk > foe1.atk, f"Room 10 foe should be stronger than Room 5: {foe2.atk} > {foe1.atk}"


def test_foe_level_cumulative_progression():
    """Foe level should never decrease across floor transitions."""
    foe1 = FoeBase()
    foe1.set_base_stat('atk', 100)
    foe1.set_base_stat('defense', 50)
    foe1.set_base_stat('max_hp', 1000)
    foe1.hp = 1000

    foe2 = FoeBase()
    foe2.set_base_stat('atk', 100)
    foe2.set_base_stat('defense', 50)
    foe2.set_base_stat('max_hp', 1000)
    foe2.hp = 1000

    node1 = MapNode(room_id=45, room_type="battle-normal", floor=1, index=45, loop=1, pressure=0)
    node2 = MapNode(room_id=1, room_type="battle-normal", floor=2, index=1, loop=1, pressure=0)

    random.seed(42)
    _scale_stats(foe1, node1)
    random.seed(42)
    _scale_stats(foe2, node2)

    assert foe2.level >= foe1.level, (
        f"Floor 2 Room 1 foe level {foe2.level} should be ≥ Floor 1 Room 45 foe level {foe1.level}"
    )


def test_cumulative_room_calculation():
    """Test that cumulative room calculation matches expected values."""
    # Floor 1, Room 1 should be cumulative room 1
    node1 = MapNode(room_id=1, room_type="battle-normal", floor=1, index=1, loop=1, pressure=0)
    cumulative1 = (node1.floor - 1) * MapGenerator.rooms_per_floor + node1.index
    assert cumulative1 == 1, f"Floor 1 Room 1 should be cumulative room 1, got {cumulative1}"

    # Floor 2, Room 1 should be cumulative room 46 (45 + 1)
    node2 = MapNode(room_id=1, room_type="battle-normal", floor=2, index=1, loop=1, pressure=0)
    cumulative2 = (node2.floor - 1) * MapGenerator.rooms_per_floor + node2.index
    assert cumulative2 == 46, f"Floor 2 Room 1 should be cumulative room 46, got {cumulative2}"

    # Floor 2, Room 10 should be cumulative room 55 (45 + 10)
    node3 = MapNode(room_id=10, room_type="battle-normal", floor=2, index=10, loop=1, pressure=0)
    cumulative3 = (node3.floor - 1) * MapGenerator.rooms_per_floor + node3.index
    assert cumulative3 == 55, f"Floor 2 Room 10 should be cumulative room 55, got {cumulative3}"


if __name__ == "__main__":
    test_cumulative_room_calculation()
    test_foe_scaling_cumulative_rooms()
    test_foe_scaling_room_progression_within_floor()
    print("All foe scaling tests passed!")
