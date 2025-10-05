from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from autofighter.mapgen import MapGenerator


class _BossRushParty:
    def __init__(self) -> None:
        self.run_config = {"run_type": {"id": "boss_rush"}}
        self.boss_rush = True


def test_generator_deterministic():
    gen1 = MapGenerator("seed")
    gen2 = MapGenerator("seed")
    rooms1 = gen1.generate_floor()
    rooms2 = gen2.generate_floor()
    assert [n.room_type for n in rooms1] == [n.room_type for n in rooms2]
    assert len(rooms1) == 10
    assert rooms1[0].room_type == "start"
    assert rooms1[-1].room_type == "battle-boss-floor"
    types = [n.room_type for n in rooms1[1:-1]]
    assert set(types) <= {"shop", "battle-weak", "battle-normal"}
    assert "shop" in types


def test_generator_boss_rush_floor_all_bosses():
    party = _BossRushParty()
    gen = MapGenerator("seed")
    rooms = gen.generate_floor(party)
    assert len(rooms) == MapGenerator.rooms_per_floor
    assert rooms[0].room_type == "start"
    assert all(room.room_type == "battle-boss-floor" for room in rooms[1:])
