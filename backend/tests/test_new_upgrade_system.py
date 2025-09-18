import importlib.util
from pathlib import Path

import pytest
import sqlcipher3

POINTS_VALUES = {1: 1, 2: 150, 3: 22500, 4: 3375000}

@pytest.fixture()
def app_with_db(tmp_path, monkeypatch):
    db_path = tmp_path / "save.db"
    monkeypatch.setenv("AF_DB_PATH", str(db_path))
    monkeypatch.setenv("AF_DB_KEY", "testkey")
    monkeypatch.syspath_prepend(Path(__file__).resolve().parents[1])
    import runs.encryption as encryption

    encryption.SAVE_MANAGER = None
    encryption.FERNET = None
    spec = importlib.util.spec_from_file_location(
        "app", Path(__file__).resolve().parents[1] / "app.py",
    )
    app_module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(app_module)
    app_module.app.testing = True
    conn = sqlcipher3.connect(db_path)
    conn.execute("PRAGMA key = 'testkey'")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS damage_types (id TEXT PRIMARY KEY, type TEXT)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS upgrade_items (id TEXT PRIMARY KEY, count INTEGER NOT NULL)"
    )
    # Set up a non-player character (ally) with fire damage type
    conn.execute(
        "INSERT OR REPLACE INTO damage_types (id, type) VALUES (?, ?)",
        ("ally", "fire"),
    )
    # Add some upgrade items for testing
    conn.execute(
        "INSERT OR REPLACE INTO upgrade_items (id, count) VALUES (?, ?)",
        ("fire_2", 5),  # 5 2-star fire items
    )
    conn.execute(
        "INSERT OR REPLACE INTO upgrade_items (id, count) VALUES (?, ?)",
        ("dark_2", 5),  # 5 2-star dark items (in case ally gets dark)
    )
    conn.execute(
        "INSERT OR REPLACE INTO upgrade_items (id, count) VALUES (?, ?)",
        ("light_1", 10),  # 10 1-star light items for player points
    )
    conn.execute(
        "INSERT OR REPLACE INTO upgrade_items (id, count) VALUES (?, ?)",
        ("wind_1", 10),  # 10 1-star wind items for player points
    )
    conn.execute(
        "INSERT OR REPLACE INTO upgrade_items (id, count) VALUES (?, ?)",
        ("generic_1", 10),  # 10 1-star generic items for player points
    )
    conn.commit()
    conn.close()
    return app_module.app, db_path


@pytest.mark.asyncio
async def test_character_point_conversion(app_with_db):
    """Non-player characters convert items into upgrade points."""
    app, db_path = app_with_db
    client = app.test_client()

    resp = await client.post(
        "/players/ally/upgrade",
        json={"star_level": 2, "item_count": 2}
    )
    data = await resp.get_json()

    expected = POINTS_VALUES[2] * 2
    assert data["points_gained"] == expected
    assert data["total_points"] == expected
    assert data["items_consumed"]["fire_2"] == 2
    assert "upgrades_applied" not in data


@pytest.mark.asyncio
async def test_player_points_system(app_with_db):
    """Player character also converts items into upgrade points."""
    app, db_path = app_with_db
    client = app.test_client()

    resp = await client.post(
        "/players/player/upgrade",
        json={"star_level": 1, "item_count": 5}
    )
    data = await resp.get_json()

    assert data["points_gained"] == 5
    assert data["total_points"] == 5


@pytest.mark.asyncio
async def test_player_spend_points_cost_curve(app_with_db):
    """Player stat upgrades follow the rising cost curve."""
    app, db_path = app_with_db
    client = app.test_client()

    resp = await client.get("/players/player/upgrade")
    initial_data = await resp.get_json()
    initial_points = initial_data.get("upgrade_points", 0)

    resp = await client.post(
        "/players/player/upgrade",
        json={"star_level": 1, "item_count": 10}
    )
    data = await resp.get_json()
    total_after_gain = initial_points + 10
    assert data["total_points"] == total_after_gain

    resp = await client.post(
        "/players/player/upgrade-stat",
        json={"stat_name": "max_hp"}
    )
    first_upgrade = await resp.get_json()

    assert first_upgrade["stat_upgraded"] == "max_hp"
    assert first_upgrade["points_spent"] == 1
    assert first_upgrade["upgrade_percent"] == pytest.approx(0.001)
    assert first_upgrade["remaining_points"] == total_after_gain - 1
    assert first_upgrade["stat_counts"]["max_hp"] == 1
    assert first_upgrade["next_costs"]["max_hp"] == 3

    resp = await client.post(
        "/players/player/upgrade-stat",
        json={"stat_name": "max_hp"}
    )
    second_upgrade = await resp.get_json()

    assert second_upgrade["points_spent"] == 3
    assert second_upgrade["upgrade_percent"] == pytest.approx(0.003)
    assert second_upgrade["remaining_points"] == total_after_gain - 4
    assert second_upgrade["stat_counts"]["max_hp"] == 2
    assert second_upgrade["stat_totals"]["max_hp"] == pytest.approx(0.004)
    assert second_upgrade["next_costs"]["max_hp"] == 5


@pytest.mark.asyncio
async def test_ally_spend_points(app_with_db):
    """Non-player characters can also spend points."""
    app, db_path = app_with_db
    client = app.test_client()

    await client.post(
        "/players/ally/upgrade",
        json={"star_level": 2, "item_count": 1}
    )

    resp = await client.post(
        "/players/ally/upgrade-stat",
        json={"stat_name": "atk"}
    )
    data = await resp.get_json()

    assert data["stat_upgraded"] == "atk"
    assert data["points_spent"] == 1
    assert data["stat_counts"]["atk"] == 1
    assert data["next_costs"]["atk"] == 3


@pytest.mark.asyncio
async def test_new_upgrade_data_in_get_endpoint(app_with_db):
    """GET endpoint surfaces upgrades and points."""
    app, db_path = app_with_db
    client = app.test_client()

    await client.post(
        "/players/ally/upgrade",
        json={"star_level": 2, "item_count": 1}
    )
    await client.post(
        "/players/ally/upgrade-stat",
        json={"stat_name": "atk"}
    )

    resp = await client.get("/players/ally/upgrade")
    data = await resp.get_json()

    assert data["upgrade_points"] == POINTS_VALUES[2] - 1
    assert data["stat_totals"]["atk"] == pytest.approx(0.001)
    assert data["stat_counts"]["atk"] == 1
    assert data["next_costs"]["atk"] == 3


@pytest.mark.asyncio
async def test_insufficient_items_error(app_with_db):
    """Test error handling for insufficient items."""
    app, db_path = app_with_db
    client = app.test_client()

    # Try to upgrade with more items than available
    resp = await client.post(
        "/players/ally/upgrade",
        json={"star_level": 2, "item_count": 10}  # Only have 5 fire_2 items
    )
    data = await resp.get_json()

    assert resp.status_code == 400
    assert "error" in data
    assert "insufficient" in data["error"]


@pytest.mark.asyncio
async def test_invalid_star_level(app_with_db):
    """Test error handling for invalid star levels."""
    app, db_path = app_with_db
    client = app.test_client()

    # Try invalid star level
    resp = await client.post(
        "/players/ally/upgrade",
        json={"star_level": 5, "item_count": 1}  # 5-star not valid
    )
    data = await resp.get_json()

    assert resp.status_code == 400
    assert "error" in data
    assert "invalid star_level" in data["error"]


@pytest.mark.asyncio
async def test_invalid_stat_name_for_points(app_with_db):
    """Test error handling for invalid stat names when spending points."""
    app, db_path = app_with_db
    client = app.test_client()

    # First gain some points
    await client.post(
        "/players/player/upgrade",
        json={"star_level": 1, "item_count": 5}
    )

    # Try to spend on invalid stat
    resp = await client.post(
        "/players/player/upgrade-stat",
        json={"stat_name": "invalid_stat", "points": 1}
    )
    data = await resp.get_json()

    assert resp.status_code == 400
    assert "error" in data
    assert "invalid stat" in data["error"]


@pytest.mark.asyncio
async def test_insufficient_points(app_with_db):
    """Test error handling for insufficient points."""
    app, db_path = app_with_db
    client = app.test_client()

    resp = await client.post(
        "/players/player/upgrade-stat",
        json={"stat_name": "max_hp"}
    )
    data = await resp.get_json()

    assert resp.status_code == 400
    assert "error" in data
    assert "insufficient upgrade points" in data["error"]
    assert data["required_points"] == 1
