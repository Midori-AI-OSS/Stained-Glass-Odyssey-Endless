"""Integration tests for idle game systems.

Tests integration between mapgen, rooms, summons, and game_state.
"""

import sys
from pathlib import Path

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.game_state import GameState
from core.mapgen import MapGenerator
from core.summons.base import Summon
from core.summons.manager import SummonManager


class TestGameStateIntegration:
    """Test GameState integration with new systems."""
    
    def test_game_state_initialization(self):
        """Test that GameState initializes with new systems."""
        gs = GameState()
        
        # Should have map and summon systems
        assert hasattr(gs, "map_generator")
        assert hasattr(gs, "summon_manager")
        assert isinstance(gs.summon_manager, SummonManager)
        assert gs.current_floor == 1
        assert gs.current_loop == 1
    
    def test_summon_manager_in_game_state(self):
        """Test summon manager operations in game state."""
        gs = GameState()
        
        # Create a summon
        summon = Summon(
            hp=100,
            summoner_id="player_1",
            summon_type="test",
        )
        
        # Add to manager
        gs.summon_manager.add_summon(summon)
        
        assert gs.summon_manager.count_summons() == 1
        assert gs.summon_manager.get_summon(summon.instance_id) == summon
        
        # Remove summon
        removed = gs.summon_manager.remove_summon(summon.instance_id)
        assert removed == summon
        assert gs.summon_manager.count_summons() == 0


class TestMapGeneratorIntegration:
    """Test MapGenerator integration."""
    
    def test_create_map_generator(self):
        """Test creating and using map generator."""
        gen = MapGenerator(seed="test", floor=1, loop=1)
        
        # Generate a floor
        nodes = gen.generate_floor()
        
        assert len(nodes) > 0
        assert nodes[0].room_type == "start"
        assert nodes[-1].room_type == "battle-boss"
    
    def test_map_generator_with_game_state(self):
        """Test using map generator with game state."""
        gs = GameState()
        
        # Create and assign map generator
        gs.map_generator = MapGenerator(
            seed="integration_test",
            floor=gs.current_floor,
            loop=gs.current_loop,
        )
        
        # Generate map
        gs.current_map = gs.map_generator.generate_floor()
        
        assert len(gs.current_map) > 0
        assert gs.current_room_index == 0


class TestSystemsIntegration:
    """Test integration between multiple systems."""
    
    def test_summons_with_map_progression(self):
        """Test that summons work alongside map progression."""
        gs = GameState()
        
        # Setup map
        gs.map_generator = MapGenerator(seed="test", floor=1)
        gs.current_map = gs.map_generator.generate_floor()
        
        # Add summons - one permanent, one temporary
        summon1 = Summon(
            hp=100,
            summoner_id="player_1",
            summon_type="minion",
            is_temporary=False,
            turns_remaining=-1,
        )
        summon2 = Summon(
            hp=50,
            summoner_id="player_1",
            summon_type="temporary",
            is_temporary=True,
            turns_remaining=2,
        )
        
        gs.summon_manager.add_summon(summon1)
        gs.summon_manager.add_summon(summon2)
        
        assert gs.summon_manager.count_summons() == 2
        assert len(gs.current_map) > 0
        
        # Simulate turn progression - first tick
        despawned = gs.summon_manager.tick_all_summons()
        assert len(despawned) == 0  # Both still alive
        assert gs.summon_manager.count_summons() == 2
        
        # Second tick - temporary should have 0 turns remaining and despawn
        despawned = gs.summon_manager.tick_all_summons()
        assert len(despawned) == 1  # Temporary summon should despawn
        assert gs.summon_manager.count_summons() == 1
    
    def test_floor_progression(self):
        """Test progressing through floors."""
        gs = GameState()
        
        # Start at floor 1
        assert gs.current_floor == 1
        
        # Generate map
        gs.map_generator = MapGenerator(seed="test", floor=gs.current_floor)
        gs.current_map = gs.map_generator.generate_floor()
        initial_count = len(gs.current_map)
        
        # Progress to next floor
        gs.current_floor = 2
        gs.map_generator = MapGenerator(seed="test", floor=gs.current_floor)
        gs.current_map = gs.map_generator.generate_floor()
        
        # Should have same structure
        assert len(gs.current_map) == initial_count
        assert gs.current_floor == 2
