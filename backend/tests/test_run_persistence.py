"""Test run persistence across backend restarts."""

import json
from pathlib import Path
import sys
import tempfile
import time

import pytest

sys.path.append(str(Path(__file__).parent.parent))

from runs import encryption as enc
from runs.encryption import get_save_manager


@pytest.fixture(autouse=True)
def reset_globals():
    """Reset global state before and after each test."""
    original_save_manager = enc.SAVE_MANAGER
    original_fernet = enc.FERNET
    enc.SAVE_MANAGER = None
    enc.FERNET = None
    yield
    enc.SAVE_MANAGER = original_save_manager
    enc.FERNET = original_fernet


def test_run_persistence_across_restart():
    """Test that runs persist in database across backend restart simulation."""
    # Use a temporary database file
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
        db_path = Path(tmp_db.name)

    try:
        # Simulate first backend instance
        import os
        original_db_url = os.environ.get('DATABASE_URL')
        os.environ['DATABASE_URL'] = f'sqlite:///{db_path}'

        # Reset global state to force re-initialization
        enc.SAVE_MANAGER = None
        enc.FERNET = None

        # Get save manager (this will create the database)
        manager1 = get_save_manager()

        # Create a test run
        run_id = f'test-run-{int(time.time())}'  # Use timestamp to make it unique
        party_data = {
            "members": ["player"],
            "gold": 100,
            "relics": [],
            "cards": [],
            "exp": {"player": 0},
            "level": {"player": 1},
            "rdr": 1.0,
            "player": {"pronouns": "", "damage_type": "Light", "stats": {"hp": 0, "attack": 0, "defense": 0}}
        }
        map_data = {
            "rooms": [{"room_type": "start"}, {"room_type": "battle-normal"}],
            "current": 1,
            "battle": False,
            "awaiting_card": False,
            "awaiting_relic": False,
            "awaiting_next": False,
        }

        with manager1.connection() as conn:
            conn.execute(
                "INSERT INTO runs (id, party, map) VALUES (?, ?, ?)",
                (run_id, json.dumps(party_data), json.dumps(map_data))
            )

        # Verify run exists
        with manager1.connection() as conn:
            cur = conn.execute("SELECT id, party, map FROM runs WHERE id = ?", (run_id,))
            row = cur.fetchone()
            assert row is not None
            assert row[0] == run_id

        # Simulate backend restart by resetting global state
        enc.SAVE_MANAGER = None
        enc.FERNET = None

        # Get save manager again (simulating new backend instance)
        manager2 = get_save_manager()

        # Verify run still exists after "restart"
        with manager2.connection() as conn:
            cur = conn.execute("SELECT id, party, map FROM runs WHERE id = ?", (run_id,))
            row = cur.fetchone()
            assert row is not None
            assert row[0] == run_id

            # Verify data integrity
            loaded_party = json.loads(row[1])
            loaded_map = json.loads(row[2])
            assert loaded_party["members"] == ["player"]
            assert loaded_party["gold"] == 100
            assert loaded_map["current"] == 1
            assert loaded_map["battle"] is False

    finally:
        # Clean up
        if original_db_url:
            os.environ['DATABASE_URL'] = original_db_url
        else:
            os.environ.pop('DATABASE_URL', None)
        db_path.unlink(missing_ok=True)


def test_get_map_endpoint_after_restart():
    """Test that the /map/<run_id> endpoint works after restart."""
    import asyncio

    from services.run_service import get_map

    # Use a temporary database file
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
        db_path = Path(tmp_db.name)

    try:
        # Simulate first backend instance
        import os
        original_db_url = os.environ.get('DATABASE_URL')
        os.environ['DATABASE_URL'] = f'sqlite:///{db_path}'

        # Reset global state to force re-initialization
        enc.SAVE_MANAGER = None
        enc.FERNET = None

        # Get save manager (this will create the database)
        manager1 = get_save_manager()

        # Create a test run
        run_id = 'test-run-456'
        party_data = {
            "members": ["player"],
            "gold": 50,
            "relics": [],
            "cards": [],
            "exp": {"player": 10},
            "level": {"player": 1},
            "rdr": 1.0,
            "player": {"pronouns": "", "damage_type": "Fire", "stats": {"hp": 0, "attack": 0, "defense": 0}}
        }
        map_data = {
            "rooms": [{"room_type": "start"}, {"room_type": "battle-normal"}, {"room_type": "shop"}],
            "current": 2,
            "battle": False,
            "awaiting_card": False,
            "awaiting_relic": False,
            "awaiting_next": True,
        }

        with manager1.connection() as conn:
            conn.execute(
                "INSERT INTO runs (id, party, map) VALUES (?, ?, ?)",
                (run_id, json.dumps(party_data), json.dumps(map_data))
            )

        # Simulate backend restart
        enc.SAVE_MANAGER = None
        enc.FERNET = None

        # Test the get_map endpoint
        @pytest.mark.asyncio
        async def test_endpoint():
            response_json = await get_map(run_id)
            assert "map" in response_json
            assert "party" in response_json
            assert response_json["map"]["current"] == 2
            assert response_json["map"]["awaiting_next"] is True
            assert response_json["party"] == ["player"]

        asyncio.run(test_endpoint())

    finally:
        # Clean up
        if original_db_url:
            os.environ['DATABASE_URL'] = original_db_url
        else:
            os.environ.pop('DATABASE_URL', None)
        db_path.unlink(missing_ok=True)


def test_enhanced_map_endpoint_current_state():
    """Test that the enhanced /map/<run_id> endpoint includes current_state section."""
    import asyncio

    from services.run_service import get_map

    # Use a temporary database file
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
        db_path = Path(tmp_db.name)

    try:
        # Set up test environment
        import os
        original_db_url = os.environ.get('DATABASE_URL')
        os.environ['DATABASE_URL'] = f'sqlite:///{db_path}'

        # Reset global state
        enc.SAVE_MANAGER = None
        enc.FERNET = None

        # Get save manager
        manager = get_save_manager()

        # Create a test run with specific state
        run_id = f'test-enhanced-map-{int(time.time())}'
        party_data = {
            "members": ["player"],
            "gold": 100,
            "relics": [],
            "cards": [],
            "exp": {"player": 0},
            "level": {"player": 1},
            "rdr": 1.0,
            "player": {"pronouns": "", "damage_type": "Fire", "stats": {"hp": 0, "attack": 0, "defense": 0}}
        }
        map_data = {
            "rooms": [
                {"room_type": "start", "floor": 1, "index": 0, "room_id": 0, "loop": 1, "pressure": 0},
                {"room_type": "battle-weak", "floor": 1, "index": 1, "room_id": 1, "loop": 1, "pressure": 0},
                {"room_type": "battle-normal", "floor": 1, "index": 2, "room_id": 2, "loop": 1, "pressure": 0},
                {"room_type": "shop", "floor": 1, "index": 3, "room_id": 3, "loop": 1, "pressure": 0}
            ],
            "current": 1,  # Currently at battle-weak
            "battle": False,
            "awaiting_card": False,
            "awaiting_relic": False,
            "awaiting_next": False,
        }

        with manager.connection() as conn:
            conn.execute(
                "INSERT INTO runs (id, party, map) VALUES (?, ?, ?)",
                (run_id, json.dumps(party_data), json.dumps(map_data))
            )

        # Test the enhanced endpoint
        @pytest.mark.asyncio
        async def test_enhanced_endpoint():
            response_json = await get_map(run_id)

            # Verify traditional map and party data still exists
            assert "map" in response_json
            assert "party" in response_json
            assert response_json["map"]["current"] == 1
            assert response_json["party"] == ["player"]

            # Verify new current_state section exists
            assert "current_state" in response_json
            current_state = response_json["current_state"]

            # Test current_state provides authoritative information
            assert current_state["current_index"] == 1
            assert current_state["current_room_type"] == "battle-weak"
            assert current_state["next_room_type"] == "battle-normal"
            assert current_state["awaiting_next"] is False
            assert current_state["awaiting_card"] is False
            assert current_state["awaiting_relic"] is False

            # Verify room_data is null when no active battle
            assert current_state["room_data"] is None

        asyncio.run(test_enhanced_endpoint())

    finally:
        # Clean up
        if original_db_url:
            os.environ['DATABASE_URL'] = original_db_url
        else:
            os.environ.pop('DATABASE_URL', None)
        db_path.unlink(missing_ok=True)


def test_enhanced_map_endpoint_with_awaiting_next():
    """Test enhanced /map endpoint when awaiting_next is True."""
    import asyncio

    from services.run_service import get_map

    # Use a temporary database file
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
        db_path = Path(tmp_db.name)

    try:
        # Set up test environment
        import os
        original_db_url = os.environ.get('DATABASE_URL')
        os.environ['DATABASE_URL'] = f'sqlite:///{db_path}'

        # Reset global state
        enc.SAVE_MANAGER = None
        enc.FERNET = None

        # Get save manager
        manager = get_save_manager()

        # Create a test run in awaiting_next state
        run_id = f'test-awaiting-next-{int(time.time())}'
        party_data = {
            "members": ["player"],
            "gold": 50,
            "relics": [],
            "cards": [],
            "exp": {"player": 0},
            "level": {"player": 1},
            "rdr": 1.0,
            "player": {"pronouns": "", "damage_type": "Light", "stats": {"hp": 0, "attack": 0, "defense": 0}}
        }
        map_data = {
            "rooms": [
                {"room_type": "start", "floor": 1, "index": 0, "room_id": 0, "loop": 1, "pressure": 0},
                {"room_type": "battle-weak", "floor": 1, "index": 1, "room_id": 1, "loop": 1, "pressure": 0},
                {"room_type": "shop", "floor": 1, "index": 2, "room_id": 2, "loop": 1, "pressure": 0}
            ],
            "current": 1,  # Currently at battle-weak
            "battle": False,
            "awaiting_card": False,
            "awaiting_relic": False,
            "awaiting_next": True,  # Waiting for next room
        }

        with manager.connection() as conn:
            conn.execute(
                "INSERT INTO runs (id, party, map) VALUES (?, ?, ?)",
                (run_id, json.dumps(party_data), json.dumps(map_data))
            )

        # Test the enhanced endpoint with awaiting_next
        @pytest.mark.asyncio
        async def test_awaiting_next():
            response_json = await get_map(run_id)
            current_state = response_json["current_state"]

            # Verify awaiting_next state is correctly reported
            assert current_state["awaiting_next"] is True
            assert current_state["current_index"] == 1
            assert current_state["current_room_type"] == "battle-weak"
            assert current_state["next_room_type"] == "shop"

            # Verify room_data includes awaiting info
            room_data = current_state["room_data"]
            assert room_data is not None
            assert room_data["awaiting_next"] is True
            assert room_data["current_room"] == "battle-weak"
            assert room_data["next_room"] == "shop"
            assert room_data.get("tags") == []

        asyncio.run(test_awaiting_next())

    finally:
        # Clean up
        if original_db_url:
            os.environ['DATABASE_URL'] = original_db_url
        else:
            os.environ.pop('DATABASE_URL', None)
        db_path.unlink(missing_ok=True)


def test_run_not_found():
    """Test that non-existent runs return 404."""
    import asyncio

    from services.run_service import get_map

    # Use a temporary database file
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
        db_path = Path(tmp_db.name)

    try:
        import os
        original_db_url = os.environ.get('DATABASE_URL')
        os.environ['DATABASE_URL'] = f'sqlite:///{db_path}'

        # Reset global state
        enc.SAVE_MANAGER = None
        enc.FERNET = None

        # Initialize empty database
        get_save_manager()

        # Test with non-existent run
        @pytest.mark.asyncio
        async def test_endpoint():
            with pytest.raises(ValueError):
                await get_map('nonexistent-run')

        asyncio.run(test_endpoint())

    finally:
        # Clean up
        if original_db_url:
            os.environ['DATABASE_URL'] = original_db_url
        else:
            os.environ.pop('DATABASE_URL', None)
        db_path.unlink(missing_ok=True)
