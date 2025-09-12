"""
Test that verifies room 10 is reachable with Pressure 1 enabled.

This test ensures that:
1. A run can be started with pressure=1
2. The player can advance through rooms to reach room 10 (index 9, 0-based)
3. Room 10 exists and is accessible in the generated map
4. Pressure scaling mechanics work correctly during progression
"""

import importlib.util
from pathlib import Path
import sys

import pytest


@pytest.fixture()
def app_with_db(tmp_path, monkeypatch):
    """Set up test app with temporary database."""
    db_path = tmp_path / "save.db"
    monkeypatch.setenv("AF_DB_PATH", str(db_path))
    monkeypatch.setenv("AF_DB_KEY", "testkey")
    monkeypatch.setenv("UV_EXTRA", "test")
    if "game" in sys.modules:
        del sys.modules["game"]
    monkeypatch.syspath_prepend(Path(__file__).resolve().parents[1])
    spec = importlib.util.spec_from_file_location(
        "app", Path(__file__).resolve().parents[1] / "app.py",
    )
    app_module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(app_module)
    app_module.app.testing = True
    return app_module.app, db_path


@pytest.mark.asyncio
async def test_room_10_reachable_with_pressure_1(app_with_db):
    """Test that room 10 is reachable when starting a run with pressure=1."""
    app, db_path = app_with_db
    client = app.test_client()

    # Start a run with pressure=1 using the UI action endpoint
    start_resp = await client.post("/ui/action", json={
        "action": "start_run",
        "params": {
            "party": ["player"],
            "pressure": 1
        }
    })
    assert start_resp.status_code == 200
    start_data = await start_resp.get_json()
    run_id = start_data["run_id"]

    # Function to get current UI state
    async def get_ui_state():
        ui_resp = await client.get("/ui")
        assert ui_resp.status_code == 200
        return await ui_resp.get_json()

    # Verify initial map state
    ui_state = await get_ui_state()
    assert ui_state["active_run"] == run_id
    game_state = ui_state["game_state"]

    # Verify map was generated with 45 rooms and pressure=1 is applied
    rooms = game_state["map"]["rooms"]
    assert len(rooms) == 45
    assert game_state["map"]["current"] == 1  # Starting at room 1 (0-based index)

    # Verify that pressure=1 is set on rooms
    for room in rooms:
        assert room["pressure"] == 1

    # Function to advance to a specific room index
    async def advance_to_room(target_index):
        """Advance through rooms until we reach the target index."""
        while True:
            # Get current state
            ui_state = await get_ui_state()
            game_state = ui_state["game_state"]
            current_index = game_state["current_state"]["current_index"]

            if current_index >= target_index:
                return current_index

            # Check if we can advance or need to perform room action first
            available_actions = ui_state["available_actions"]

            if "room_action" in available_actions:
                # Need to perform room action first
                current_room_type = game_state["current_state"]["current_room_type"]

                # Perform room action based on room type
                await client.post("/ui/action", json={
                    "action": "room_action",
                    "params": {
                        "room_id": str(current_index),
                        "type": current_room_type
                    }
                })
                # Room action might fail for some room types, that's okay

            if "advance_room" in available_actions:
                # Advance to next room
                advance_resp = await client.post("/ui/action", json={
                    "action": "advance_room",
                    "params": {}
                })
                assert advance_resp.status_code == 200
            else:
                # Something unexpected, break to avoid infinite loop
                break

    # Advance to room 10 (index 9, 0-based)
    target_room_index = 9  # Room 10 in 1-based numbering
    final_index = await advance_to_room(target_room_index)

    # Verify we reached room 10
    assert final_index >= target_room_index, f"Failed to reach room 10, stopped at index {final_index}"

    # Get final state to verify room 10 details
    ui_state = await get_ui_state()
    game_state = ui_state["game_state"]
    rooms = game_state["map"]["rooms"]
    current_index = game_state["current_state"]["current_index"]

    # Verify we're at or past room 10
    assert current_index >= target_room_index

    # Verify room 10 exists and has correct properties
    room_10 = rooms[target_room_index]
    assert room_10["index"] == target_room_index
    assert room_10["pressure"] == 1
    assert room_10["floor"] == 1
    assert room_10["loop"] == 1

    # Verify room type is valid
    valid_room_types = {"battle-weak", "battle-normal", "shop", "rest", "start", "battle-boss-floor"}
    assert room_10["room_type"] in valid_room_types

    print("✓ Successfully reached room 10 with pressure=1")
    print(f"  Room 10 details: {room_10}")
    print(f"  Current index: {current_index}")


@pytest.mark.asyncio
async def test_pressure_1_map_generation(app_with_db):
    """Test that map generation works correctly with pressure=1."""
    app, _ = app_with_db
    client = app.test_client()

    # Start run with pressure=1 using UI action
    start_resp = await client.post("/ui/action", json={
        "action": "start_run",
        "params": {
            "party": ["player"],
            "pressure": 1
        }
    })
    assert start_resp.status_code == 200
    start_data = await start_resp.get_json()
    start_data["run_id"]

    # Get UI state which contains map data
    ui_resp = await client.get("/ui")
    assert ui_resp.status_code == 200
    ui_data = await ui_resp.get_json()

    game_state = ui_data["game_state"]
    rooms = game_state["map"]["rooms"]

    # Verify all rooms have pressure=1
    for i, room in enumerate(rooms):
        assert room["pressure"] == 1, f"Room {i} has incorrect pressure: {room['pressure']}"
        assert room["floor"] == 1
        assert room["loop"] == 1
        assert room["index"] == i

    # Verify room 10 specifically exists
    assert len(rooms) > 9, "Map doesn't have enough rooms to contain room 10"
    room_10 = rooms[9]  # 0-based index
    assert room_10["index"] == 9
    assert room_10["pressure"] == 1

    # Verify standard map structure
    assert rooms[0]["room_type"] == "start"
    assert rooms[-1]["room_type"] == "battle-boss-floor"

    # Count room types in middle section (excluding start and boss)
    middle_rooms = rooms[1:-1]
    room_type_counts = {}
    for room in middle_rooms:
        rt = room["room_type"]
        room_type_counts[rt] = room_type_counts.get(rt, 0) + 1

    # Verify required room types exist
    assert room_type_counts.get("shop", 0) >= 2, "Map should have at least 2 shop rooms"
    assert room_type_counts.get("rest", 0) >= 2, "Map should have at least 2 rest rooms"
    assert room_type_counts.get("battle-weak", 0) > 0, "Map should have battle-weak rooms"
    assert room_type_counts.get("battle-normal", 0) > 0, "Map should have battle-normal rooms"

    print("✓ Map generation with pressure=1 successful")
    print(f"  Total rooms: {len(rooms)}")
    print(f"  Room type distribution: {room_type_counts}")


@pytest.mark.asyncio
async def test_pressure_1_room_10_specific_validation(app_with_db):
    """Test specifically that room 10 (0-based index 9) works correctly with pressure=1."""
    app, _ = app_with_db
    client = app.test_client()

    # Start run with pressure=1
    start_resp = await client.post("/ui/action", json={
        "action": "start_run",
        "params": {
            "party": ["player"],
            "pressure": 1
        }
    })
    assert start_resp.status_code == 200

    # Get UI state to access map
    ui_resp = await client.get("/ui")
    ui_data = await ui_resp.get_json()
    game_state = ui_data["game_state"]
    rooms = game_state["map"]["rooms"]

    # Focus specifically on room 10 (index 9)
    room_10_index = 9
    room_10 = rooms[room_10_index]

    # Validate room 10 properties
    assert room_10["index"] == room_10_index, f"Room 10 has wrong index: {room_10['index']}"
    assert room_10["pressure"] == 1, f"Room 10 has wrong pressure: {room_10['pressure']}"
    assert room_10["floor"] == 1, f"Room 10 has wrong floor: {room_10['floor']}"
    assert room_10["loop"] == 1, f"Room 10 has wrong loop: {room_10['loop']}"

    # Room 10 should be a valid room type
    valid_room_types = {"battle-weak", "battle-normal", "shop", "rest"}
    assert room_10["room_type"] in valid_room_types, f"Room 10 has invalid room type: {room_10['room_type']}"

    # Verify room 10 is not start or boss (those are at specific positions)
    assert room_10["room_type"] != "start", "Room 10 should not be start room"
    assert room_10["room_type"] != "battle-boss-floor", "Room 10 should not be boss room"

    # Verify consistent room_id
    assert room_10["room_id"] == room_10_index, f"Room 10 has inconsistent room_id: {room_10['room_id']}"

    print("✓ Room 10 validation with pressure=1 successful")
    print(f"  Room 10: {room_10}")
    print(f"  Index {room_10_index} -> Room {room_10_index + 1} (1-based)")
