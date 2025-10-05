from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.run_configuration import build_run_modifier_context
from services.run_configuration import validate_run_configuration

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


def test_generator_marks_prime_glitched_and_bonus_rooms():
    selection = validate_run_configuration(
        run_type="standard",
        modifiers={"pressure": 12, "foe_prime_rate": 6, "foe_glitched_rate": 6},
    )
    context = build_run_modifier_context(selection.snapshot)
    gen = MapGenerator("seed", modifier_context=context, configuration=selection.snapshot)
    rooms = gen.generate_floor()
    battle_rooms = [room for room in rooms if room.room_type.startswith("battle")]

    assert any("prime" in room.room_type for room in battle_rooms)
    assert any("glitched" in room.room_type for room in battle_rooms)
    assert any(
        room.encounter_bonus_marker for room in battle_rooms if room.room_type != "battle-boss-floor"
    )

    for room in battle_rooms:
        if room.room_type == "battle-boss-floor":
            continue
        if "prime" in room.room_type:
            assert room.prime_bonus_pct >= context.prime_spawn_bonus_pct
        if "glitched" in room.room_type:
            assert room.glitched_bonus_pct >= context.glitched_spawn_bonus_pct
        assert room.elite_bonus_pct >= context.elite_spawn_bonus_pct
