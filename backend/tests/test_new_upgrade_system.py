import importlib.util
from pathlib import Path

import pytest
import sqlcipher3

STAR_TO_MATERIALS = {1: 1, 2: 150, 3: 22500, 4: 3375000}


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
    conn.execute(
        "INSERT OR REPLACE INTO damage_types (id, type) VALUES (?, ?)",
        ("ally", "fire"),
    )
    conn.execute(
        "INSERT OR REPLACE INTO damage_types (id, type) VALUES (?, ?)",
        ("player", "light"),
    )
    starting_items = {
        "fire_2": 5,
        "fire_1": 10,
        "light_1": 10,
        "generic_1": 10,
        "generic_2": 2,
    }
    for key, value in starting_items.items():
        conn.execute(
            "INSERT OR REPLACE INTO upgrade_items (id, count) VALUES (?, ?)",
            (key, value),
        )
    conn.commit()
    conn.close()
    return app_module.app, db_path


def _fetch_item_counts(db_path):
    conn = sqlcipher3.connect(db_path)
    conn.execute("PRAGMA key = 'testkey'")
    cur = conn.execute("SELECT id, count FROM upgrade_items")
    data = {row[0]: int(row[1]) for row in cur.fetchall()}
    conn.close()
    return data


@pytest.mark.asyncio
async def test_character_material_conversion(app_with_db):
    app, db_path = app_with_db
    client = app.test_client()

    resp = await client.post(
        "/players/ally/upgrade",
        json={"star_level": 2, "item_count": 2},
    )
    data = await resp.get_json()

    assert resp.status_code == 200
    assert data["materials_gained"] == STAR_TO_MATERIALS[2] * 2
    assert data["items_consumed"] == {"fire_2": 2}
    assert data["material_key"] == "fire_1"
    assert data["materials_balance"] == 10 + STAR_TO_MATERIALS[2] * 2

    inventory = _fetch_item_counts(db_path)
    assert inventory["fire_2"] == 3
    assert inventory["fire_1"] == 10 + STAR_TO_MATERIALS[2] * 2


@pytest.mark.asyncio
async def test_upgrade_borrows_higher_tier_materials(app_with_db):
    app, db_path = app_with_db
    client = app.test_client()

    conn = sqlcipher3.connect(db_path)
    conn.execute("PRAGMA key = 'testkey'")
    conn.execute(
        "INSERT OR REPLACE INTO upgrade_items (id, count) VALUES (?, ?)",
        ("fire_1", 210),
    )
    conn.commit()
    conn.close()

    from runs.encryption import get_save_manager

    from autofighter.gacha import GachaManager

    manager = GachaManager(get_save_manager())
    items = manager._get_items()
    manager._auto_craft(items)
    manager._set_items(items)

    resp = await client.post(
        "/players/ally/upgrade",
        json={"star_level": 1, "item_count": 200},
    )
    data = await resp.get_json()

    assert resp.status_code == 200
    assert data["materials_gained"] == STAR_TO_MATERIALS[1] * 200
    assert data["items_consumed"].get("fire_1") == 85
    assert data["items_consumed"].get("fire_2") == 1
    assert data["material_key"] == "fire_1"

    inventory = _fetch_item_counts(db_path)
    assert inventory["fire_1"] == 200
    assert inventory["fire_2"] == 5


@pytest.mark.asyncio
async def test_player_conversion_uses_active_element(app_with_db):
    app, db_path = app_with_db
    client = app.test_client()

    resp = await client.post(
        "/players/player/upgrade",
        json={"star_level": 2, "item_count": 1},
    )
    data = await resp.get_json()

    assert resp.status_code == 200
    assert data["materials_gained"] == STAR_TO_MATERIALS[2]
    assert data["material_key"] == "light_1"
    assert data["items_consumed"] == {"generic_2": 1}
    assert data["materials_balance"] == 10 + STAR_TO_MATERIALS[2]

    inventory = _fetch_item_counts(db_path)
    assert inventory["generic_2"] == 1
    assert inventory["light_1"] == 10 + STAR_TO_MATERIALS[2]


@pytest.mark.asyncio
async def test_upgrade_spends_materials_and_scales_cost(app_with_db):
    app, db_path = app_with_db
    client = app.test_client()

    # Convert generic items into light materials for the player
    await client.post(
        "/players/player/upgrade",
        json={"star_level": 2, "item_count": 2},
    )

    resp = await client.post(
        "/players/player/upgrade-stat",
        json={"stat_name": "max_hp"},
    )
    first_upgrade = await resp.get_json()

    assert resp.status_code == 200
    assert first_upgrade["stat_upgraded"] == "max_hp"
    assert first_upgrade["materials_spent"] == 1
    assert first_upgrade["upgrade_percent"] == pytest.approx(0.001)
    assert first_upgrade["completed_upgrades"] == 1
    assert first_upgrade["next_costs"]["max_hp"]["count"] == 2
    assert first_upgrade["next_costs"]["max_hp"]["item"] == "light_1"

    resp = await client.post(
        "/players/player/upgrade-stat",
        json={"stat_name": "max_hp"},
    )
    second_upgrade = await resp.get_json()

    assert second_upgrade["materials_spent"] == 2
    assert second_upgrade["completed_upgrades"] == 1
    assert second_upgrade["next_costs"]["max_hp"]["count"] == 3
    assert second_upgrade["materials_remaining"] == first_upgrade["materials_remaining"] - 2


@pytest.mark.asyncio
async def test_upgrade_respects_budget_and_partial(app_with_db):
    app, _ = app_with_db
    client = app.test_client()

    await client.post(
        "/players/player/upgrade",
        json={"star_level": 2, "item_count": 1},
    )

    resp = await client.post(
        "/players/player/upgrade-stat",
        json={"stat_name": "atk", "repeat": 3, "total_materials": 3},
    )
    data = await resp.get_json()

    assert resp.status_code == 200
    assert data["materials_spent"] == 3
    assert data["completed_upgrades"] == 2
    assert data["partial"] is True
    assert data["budget_remaining"] == 0


@pytest.mark.asyncio
async def test_invalid_material_cost_error(app_with_db):
    app, _ = app_with_db
    client = app.test_client()

    await client.post(
        "/players/player/upgrade",
        json={"star_level": 1, "item_count": 3},
    )

    resp = await client.post(
        "/players/player/upgrade-stat",
        json={"stat_name": "defense", "materials": 2},
    )
    data = await resp.get_json()

    assert resp.status_code == 400
    assert data["error"] == "invalid material cost"
    assert data["expected_materials"] == 1


@pytest.mark.asyncio
async def test_insufficient_materials_error(app_with_db):
    app, _ = app_with_db
    client = app.test_client()

    app, db_path = app_with_db
    client = app.test_client()

    conn = sqlcipher3.connect(db_path)
    conn.execute("PRAGMA key = 'testkey'")
    conn.execute(
        "INSERT OR REPLACE INTO upgrade_items (id, count) VALUES (?, ?)",
        ("light_1", 0),
    )
    conn.commit()
    conn.close()

    resp = await client.post(
        "/players/player/upgrade-stat",
        json={"stat_name": "mitigation"},
    )
    data = await resp.get_json()

    assert resp.status_code == 400
    assert data["error"] == "insufficient materials"
    assert data["required_materials"] == 1


@pytest.mark.asyncio
async def test_get_endpoint_payload_structure(app_with_db):
    app, _ = app_with_db
    client = app.test_client()

    await client.post(
        "/players/ally/upgrade",
        json={"star_level": 2, "item_count": 1},
    )
    await client.post(
        "/players/ally/upgrade-stat",
        json={"stat_name": "atk"},
    )

    resp = await client.get("/players/ally/upgrade")
    data = await resp.get_json()

    assert resp.status_code == 200
    assert "upgrade_points" not in data
    assert data["next_costs"]["atk"]["item"] == "fire_1"
    assert isinstance(data["next_costs"]["atk"]["count"], int)
    assert data["stat_counts"]["atk"] == 1
    assert data["element"] == "fire"


@pytest.mark.asyncio
async def test_migration_converts_legacy_points(app_with_db):
    app, db_path = app_with_db
    client = app.test_client()

    conn = sqlcipher3.connect(db_path)
    conn.execute("PRAGMA key = 'testkey'")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS player_upgrade_points (player_id TEXT PRIMARY KEY, points INTEGER NOT NULL)"
    )
    conn.execute(
        "INSERT OR REPLACE INTO player_upgrade_points (player_id, points) VALUES (?, ?)",
        ("ally", 10),
    )
    conn.execute(
        "INSERT OR REPLACE INTO player_upgrade_points (player_id, points) VALUES (?, ?)",
        ("player", 25),
    )
    conn.commit()
    conn.close()

    resp = await client.get("/players/player/upgrade")
    assert resp.status_code == 200

    inventory = _fetch_item_counts(db_path)
    assert inventory["fire_1"] >= 10
    assert inventory["light_1"] >= 25

    conn = sqlcipher3.connect(db_path)
    conn.execute("PRAGMA key = 'testkey'")
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='player_upgrade_points'"
    )
    assert cur.fetchone() is None
    conn.close()
