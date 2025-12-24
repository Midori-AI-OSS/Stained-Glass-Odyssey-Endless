"""Tests for summons system."""

from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.stats import Stats
from core.summons.base import Summon
from core.summons.manager import SummonManager


class TestSummon:
    """Test Summon class."""

    def test_create_summon(self):
        """Test creating a summon."""
        summon = Summon(
            hp=100,
            summoner_id="player_1",
            summon_type="minion",
            summon_source="card_summon",
        )

        assert summon.hp == 100
        assert summon.summoner_id == "player_1"
        assert summon.summon_type == "minion"
        assert summon.instance_id != ""

    def test_create_from_summoner(self):
        """Test creating summon from summoner stats."""
        summoner = Stats(hp=1000)
        # Set base stats after creation
        summoner._base_atk = 200
        summoner._base_defense = 100

        summon = Summon.create_from_summoner(
            summoner=summoner,
            summon_type="clone",
            source="passive_clone",
            stat_multiplier=0.5,
        )

        # Should have 50% of summoner's stats
        assert summon.hp == 500  # 50% of max_hp (1000)
        assert summon._base_atk == 100  # 50% of 200
        assert summon._base_defense == 50  # 50% of 100
        assert summon.summon_type == "clone"

    def test_temporary_summon(self):
        """Test temporary summon with turn limit."""
        summon = Summon(
            hp=100,
            summoner_id="player_1",
            summon_type="temporary",
            is_temporary=True,
            turns_remaining=3,
        )

        assert summon.is_temporary
        assert summon.turns_remaining == 3

        # Tick turn
        still_alive = summon.tick_turn()
        assert still_alive
        assert summon.turns_remaining == 2

        # Tick again
        still_alive = summon.tick_turn()
        assert still_alive
        assert summon.turns_remaining == 1

        # Final tick
        still_alive = summon.tick_turn()
        assert not still_alive
        assert summon.turns_remaining == 0

    def test_permanent_summon(self):
        """Test permanent summon."""
        summon = Summon(
            hp=100,
            summoner_id="player_1",
            summon_type="permanent",
            is_temporary=False,
            turns_remaining=-1,
        )

        assert not summon.is_temporary

        # Ticking should always return True
        for _ in range(10):
            still_alive = summon.tick_turn()
            assert still_alive
            assert summon.turns_remaining == -1

    def test_is_alive(self):
        """Test is_alive method."""
        summon = Summon(hp=100, summoner_id="player_1")
        assert summon.is_alive()

        summon.hp = 0
        assert not summon.is_alive()

        summon.hp = -10
        assert not summon.is_alive()

    def test_should_despawn(self):
        """Test should_despawn logic."""
        # Alive and permanent
        summon1 = Summon(
            hp=100,
            summoner_id="player_1",
            is_temporary=False,
        )
        assert not summon1.should_despawn()

        # Dead
        summon2 = Summon(
            hp=0,
            summoner_id="player_1",
        )
        assert summon2.should_despawn()

        # Expired temporary
        summon3 = Summon(
            hp=100,
            summoner_id="player_1",
            is_temporary=True,
            turns_remaining=0,
        )
        assert summon3.should_despawn()

    def test_summon_to_dict(self):
        """Test converting summon to dict."""
        summon = Summon(
            hp=100,
            summoner_id="player_1",
            summon_type="test",
            summon_source="test_card",
            turns_remaining=5,
        )

        data = summon.to_dict()

        assert data["summoner_id"] == "player_1"
        assert data["summon_type"] == "test"
        assert data["turns_remaining"] == 5
        assert "instance_id" in data

    def test_summon_from_dict(self):
        """Test creating summon from dict."""
        data = {
            "instance_id": "test_123",
            "summoner_id": "player_2",
            "summon_type": "warrior",
            "summon_source": "relic_spawn",
            "hp": 200,
            "max_hp": 200,
            "atk": 50,
            "defense": 30,
            "turns_remaining": 3,
        }

        summon = Summon.from_dict(data)

        assert summon.instance_id == "test_123"
        assert summon.summoner_id == "player_2"
        assert summon.hp == 200
        assert summon.turns_remaining == 3


class TestSummonManager:
    """Test SummonManager class."""

    def test_create_manager(self):
        """Test creating a summon manager."""
        manager = SummonManager()

        assert manager.count_summons() == 0

    def test_add_summon(self):
        """Test adding a summon."""
        manager = SummonManager()
        summon = Summon(
            hp=100,
            summoner_id="player_1",
            summon_type="minion",
        )

        manager.add_summon(summon)

        assert manager.count_summons() == 1
        assert manager.get_summon(summon.instance_id) == summon

    def test_remove_summon(self):
        """Test removing a summon."""
        manager = SummonManager()
        summon = Summon(
            hp=100,
            summoner_id="player_1",
            summon_type="minion",
        )

        manager.add_summon(summon)
        assert manager.count_summons() == 1

        removed = manager.remove_summon(summon.instance_id)

        assert removed == summon
        assert manager.count_summons() == 0
        assert manager.get_summon(summon.instance_id) is None

    def test_get_summons_by_summoner(self):
        """Test getting summons for a specific summoner."""
        manager = SummonManager()

        summon1 = Summon(hp=100, summoner_id="player_1", summon_type="minion1")
        summon2 = Summon(hp=100, summoner_id="player_1", summon_type="minion2")
        summon3 = Summon(hp=100, summoner_id="player_2", summon_type="minion3")

        manager.add_summon(summon1)
        manager.add_summon(summon2)
        manager.add_summon(summon3)

        player1_summons = manager.get_summons_by_summoner("player_1")
        player2_summons = manager.get_summons_by_summoner("player_2")

        assert len(player1_summons) == 2
        assert len(player2_summons) == 1
        assert summon1 in player1_summons
        assert summon2 in player1_summons
        assert summon3 in player2_summons

    def test_tick_all_summons(self):
        """Test ticking all summons."""
        manager = SummonManager()

        # Permanent summon
        permanent = Summon(
            hp=100,
            summoner_id="player_1",
            is_temporary=False,
        )

        # Temporary with 2 turns
        temporary = Summon(
            hp=100,
            summoner_id="player_1",
            is_temporary=True,
            turns_remaining=2,
        )

        manager.add_summon(permanent)
        manager.add_summon(temporary)

        assert manager.count_summons() == 2

        # First tick
        despawned = manager.tick_all_summons()
        assert len(despawned) == 0
        assert manager.count_summons() == 2

        # Second tick - temporary should expire
        despawned = manager.tick_all_summons()
        assert len(despawned) == 1
        assert temporary.instance_id in despawned
        assert manager.count_summons() == 1

    def test_clear_summons(self):
        """Test clearing all summons."""
        manager = SummonManager()

        summon1 = Summon(hp=100, summoner_id="player_1", summon_type="minion1")
        summon2 = Summon(hp=100, summoner_id="player_2", summon_type="minion2")

        manager.add_summon(summon1)
        manager.add_summon(summon2)

        assert manager.count_summons() == 2

        manager.clear_summons()

        assert manager.count_summons() == 0

    def test_clear_summons_for_specific_summoner(self):
        """Test clearing summons for a specific summoner."""
        manager = SummonManager()

        summon1 = Summon(hp=100, summoner_id="player_1", summon_type="minion1")
        summon2 = Summon(hp=100, summoner_id="player_1", summon_type="minion2")
        summon3 = Summon(hp=100, summoner_id="player_2", summon_type="minion3")

        manager.add_summon(summon1)
        manager.add_summon(summon2)
        manager.add_summon(summon3)

        assert manager.count_summons() == 3

        manager.clear_summons("player_1")

        assert manager.count_summons() == 1
        assert manager.count_summons("player_2") == 1

    def test_manager_to_dict(self):
        """Test converting manager to dict."""
        manager = SummonManager()

        summon = Summon(hp=100, summoner_id="player_1", summon_type="test")
        manager.add_summon(summon)

        data = manager.to_dict()

        assert "summons" in data
        assert len(data["summons"]) == 1
        assert data["summons"][0]["summoner_id"] == "player_1"

    def test_manager_from_dict(self):
        """Test creating manager from dict."""
        data = {
            "summons": [
                {
                    "instance_id": "test_123",
                    "summoner_id": "player_1",
                    "summon_type": "minion",
                    "hp": 100,
                    "max_hp": 100,
                    "atk": 20,
                    "defense": 10,
                }
            ]
        }

        manager = SummonManager.from_dict(data)

        assert manager.count_summons() == 1
        summons = manager.get_all_summons()
        assert summons[0].summoner_id == "player_1"
        assert summons[0].instance_id == "test_123"
