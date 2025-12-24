"""Tests for mapgen system."""

from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.mapgen import MapGenerator
from core.mapgen import MapNode


class TestMapNode:
    """Test MapNode dataclass."""

    def test_create_map_node(self):
        """Test creating a map node."""
        node = MapNode(
            room_id=0,
            room_type="start",
            floor=1,
            index=0,
            loop=1,
            pressure=0,
        )

        assert node.room_id == 0
        assert node.room_type == "start"
        assert node.floor == 1
        assert node.index == 0

    def test_map_node_to_dict(self):
        """Test converting map node to dict."""
        node = MapNode(
            room_id=1,
            room_type="battle-normal",
            floor=2,
            index=1,
            tags=("prime",),
        )

        data = node.to_dict()

        assert data["room_id"] == 1
        assert data["room_type"] == "battle-normal"
        assert data["floor"] == 2
        assert data["tags"] == ["prime"]

    def test_map_node_from_dict(self):
        """Test creating map node from dict."""
        data = {
            "room_id": 2,
            "room_type": "shop",
            "floor": 3,
            "index": 5,
            "tags": ["elite"],
        }

        node = MapNode.from_dict(data)

        assert node.room_id == 2
        assert node.room_type == "shop"
        assert node.floor == 3
        assert node.tags == ("elite",)


class TestMapGenerator:
    """Test MapGenerator class."""

    def test_create_generator(self):
        """Test creating a map generator."""
        gen = MapGenerator(seed="test_seed", floor=1, loop=1)

        assert gen.floor == 1
        assert gen.loop == 1
        assert gen.pressure == 0

    def test_generate_floor(self):
        """Test generating a floor."""
        gen = MapGenerator(seed="test_seed", floor=1)
        nodes = gen.generate_floor()

        # Should have exactly ROOMS_PER_FLOOR nodes
        assert len(nodes) == MapGenerator.ROOMS_PER_FLOOR

        # First should be start
        assert nodes[0].room_type == "start"

        # Last should be boss
        assert nodes[-1].room_type == "battle-boss"

        # All should have correct floor
        for node in nodes:
            assert node.floor == 1

    def test_generate_boss_rush(self):
        """Test generating a boss rush floor."""
        gen = MapGenerator(seed="test_seed", floor=1)
        nodes = gen.generate_floor(boss_rush=True)

        # Should have exactly ROOMS_PER_FLOOR nodes
        assert len(nodes) == MapGenerator.ROOMS_PER_FLOOR

        # First should be start
        assert nodes[0].room_type == "start"

        # Rest should be bosses
        for node in nodes[1:]:
            assert node.room_type == "battle-boss"

    def test_deterministic_generation(self):
        """Test that same seed produces same floor."""
        gen1 = MapGenerator(seed="same_seed", floor=1)
        nodes1 = gen1.generate_floor()

        gen2 = MapGenerator(seed="same_seed", floor=1)
        nodes2 = gen2.generate_floor()

        # Should be identical
        assert len(nodes1) == len(nodes2)
        for n1, n2 in zip(nodes1, nodes2):
            assert n1.room_type == n2.room_type
            assert n1.floor == n2.floor
            assert n1.index == n2.index

    def test_different_seeds_different_floors(self):
        """Test that different seeds produce different floors."""
        gen1 = MapGenerator(seed="seed1", floor=1)
        nodes1 = gen1.generate_floor()

        gen2 = MapGenerator(seed="seed2", floor=1)
        nodes2 = gen2.generate_floor()

        # Should have some differences in room types
        # (not guaranteed but highly likely with different seeds)
        middle1 = [n.room_type for n in nodes1[1:-1]]
        middle2 = [n.room_type for n in nodes2[1:-1]]
        assert middle1 != middle2

    def test_shop_rooms_present(self):
        """Test that shop rooms are generated."""
        gen = MapGenerator(seed="test_seed", floor=1)
        nodes = gen.generate_floor()

        # Should have at least one shop
        room_types = [n.room_type for n in nodes]
        assert "shop" in room_types

    def test_battle_rooms_present(self):
        """Test that battle rooms are generated."""
        gen = MapGenerator(seed="test_seed", floor=1)
        nodes = gen.generate_floor()

        # Should have various battle types
        room_types = [n.room_type for n in nodes]
        battle_rooms = [rt for rt in room_types if rt.startswith("battle")]

        # Most rooms should be battles
        assert len(battle_rooms) > len(nodes) // 2

    def test_pressure_scaling(self):
        """Test that pressure is applied to nodes."""
        gen = MapGenerator(seed="test_seed", floor=1, pressure=5)
        nodes = gen.generate_floor()

        # All nodes should have pressure
        for node in nodes:
            assert node.pressure == 5

    def test_floor_scaling(self):
        """Test generating floors at different levels."""
        # Floor 1
        gen1 = MapGenerator(seed="test_seed", floor=1)
        nodes1 = gen1.generate_floor()

        # Floor 10
        gen10 = MapGenerator(seed="test_seed", floor=10)
        nodes10 = gen10.generate_floor()

        # Both should have same structure
        assert len(nodes1) == len(nodes10)

        # Floor numbers should match
        for node in nodes1:
            assert node.floor == 1
        for node in nodes10:
            assert node.floor == 10
