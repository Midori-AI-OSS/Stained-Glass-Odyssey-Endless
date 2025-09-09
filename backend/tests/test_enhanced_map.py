"""Test enhanced map endpoint functionality."""

import importlib.util
from pathlib import Path
import sys

import pytest


@pytest.fixture()
def app_with_db(tmp_path, monkeypatch):
    db_path = tmp_path / "save.db"
    monkeypatch.setenv("AF_DB_PATH", str(db_path))
    monkeypatch.setenv("AF_DB_KEY", "testkey")
    monkeypatch.setenv("UV_EXTRA", "test")
    if "game" in sys.modules:
        del sys.modules["game"]
    monkeypatch.syspath_prepend(Path(__file__).resolve().parents[1])
    spec = importlib.util.spec_from_file_location(
        "app",
        Path(__file__).resolve().parents[1] / "app.py",
    )
    app_module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(app_module)
    app_module.app.testing = True
    return app_module.app, db_path


@pytest.mark.asyncio
async def test_enhanced_map_endpoint_current_state(app_with_db):
    """Test that the enhanced /map/<run_id> endpoint includes current_state section."""
    app, _ = app_with_db
    client = app.test_client()

    # Start a run to test
    start_resp = await client.post("/run/start", json={"party": ["player"]})
    start_data = await start_resp.get_json()
    run_id = start_data["run_id"]

    # Get the enhanced map data
    map_resp = await client.get(f"/map/{run_id}")
    assert map_resp.status_code == 200

    map_data = await map_resp.get_json()

    # Verify traditional map and party data still exists
    assert "map" in map_data
    assert "party" in map_data
    assert isinstance(map_data["map"]["current"], int)
    assert isinstance(map_data["party"], list)

    # Verify new current_state section exists
    assert "current_state" in map_data
    current_state = map_data["current_state"]

    # Test current_state provides authoritative information
    assert "current_index" in current_state
    assert "current_room_type" in current_state
    assert "next_room_type" in current_state
    assert "awaiting_next" in current_state
    assert "awaiting_card" in current_state
    assert "awaiting_relic" in current_state
    assert "room_data" in current_state

    # Verify the current state values are reasonable
    assert isinstance(current_state["current_index"], int)
    assert current_state["current_index"] >= 0
    assert current_state["current_room_type"] is not None
    assert isinstance(current_state["awaiting_next"], bool)
    assert isinstance(current_state["awaiting_card"], bool)
    assert isinstance(current_state["awaiting_relic"], bool)


@pytest.mark.asyncio
async def test_enhanced_map_endpoint_battle_state(app_with_db):
    """Test enhanced map endpoint with active battle state."""
    app, _ = app_with_db
    client = app.test_client()

    # Start a run
    start_resp = await client.post("/run/start", json={"party": ["player"]})
    start_data = await start_resp.get_json()
    run_id = start_data["run_id"]

    # Enter a battle room to get battle state
    battle_resp = await client.post(f"/rooms/{run_id}/battle", json={"action": ""})
    battle_data = await battle_resp.get_json()

    # Only test if we successfully entered battle
    if battle_resp.status_code == 200 and battle_data.get("result") == "battle":
        # Get the enhanced map data during battle
        map_resp = await client.get(f"/map/{run_id}")
        assert map_resp.status_code == 200

        map_data = await map_resp.get_json()
        current_state = map_data["current_state"]

        # Verify battle data is included
        if current_state["room_data"] is not None:
            room_data = current_state["room_data"]
            assert room_data["result"] == "battle"
            # Battle data should include party and foes information
            assert "party" in room_data or "foes" in room_data


@pytest.mark.asyncio
async def test_enhanced_map_backend_authority(app_with_db):
    """Test that backend state is authoritative and consistent."""
    app, _ = app_with_db
    client = app.test_client()

    # Start a run
    start_resp = await client.post("/run/start", json={"party": ["player"]})
    start_data = await start_resp.get_json()
    run_id = start_data["run_id"]

    # Get current state
    map_resp = await client.get(f"/map/{run_id}")
    map_data = await map_resp.get_json()

    # Verify consistency between map state and current_state
    map_current = map_data["map"]["current"]
    current_state_index = map_data["current_state"]["current_index"]

    assert (
        map_current == current_state_index
    ), "Backend map.current should match current_state.current_index"

    # Verify room type consistency
    if map_data["map"]["rooms"] and current_state_index < len(map_data["map"]["rooms"]):
        expected_room_type = map_data["map"]["rooms"][current_state_index]["room_type"]
        actual_room_type = map_data["current_state"]["current_room_type"]
        assert (
            expected_room_type == actual_room_type
        ), "Room type should be consistent between map and current_state"
