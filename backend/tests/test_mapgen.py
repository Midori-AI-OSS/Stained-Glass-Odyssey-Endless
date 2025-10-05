from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from autofighter.mapgen import MapGenerator
from services.run_configuration import build_run_modifier_context
from services.run_configuration import validate_run_configuration


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
    selection = validate_run_configuration(run_type="boss_rush", modifiers={"pressure": 5})
    context = build_run_modifier_context(selection.snapshot)
    gen = MapGenerator("seed", modifier_context=context, configuration=selection.snapshot)
    rooms = gen.generate_floor(party)
    assert len(rooms) == MapGenerator.rooms_per_floor
    assert rooms[0].room_type == "start"
    assert all(room.room_type == "battle-boss-floor" for room in rooms[1:])


def test_generator_attaches_modifier_context_metadata():
    selection = validate_run_configuration(run_type="standard", modifiers={"pressure": 3})
    context = build_run_modifier_context(selection.snapshot)
    gen = MapGenerator("seed", modifier_context=context, configuration=selection.snapshot)
    rooms = gen.generate_floor()
    assert rooms[0].modifier_context["metadata_hash"] == context.metadata_hash
    assert rooms[0].metadata_hash == context.metadata_hash
