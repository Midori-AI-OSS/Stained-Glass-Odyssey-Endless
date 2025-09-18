import importlib.util

from pathlib import Path
from unittest.mock import patch

import pytest
import sqlcipher3


@pytest.fixture()
def app_with_db(tmp_path, monkeypatch):
    db_path = tmp_path / "save.db"
    monkeypatch.setenv("AF_DB_PATH", str(db_path))
    monkeypatch.setenv("AF_DB_KEY", "testkey")
    monkeypatch.syspath_prepend(Path(__file__).resolve().parents[1])
    spec = importlib.util.spec_from_file_location(
        "app", Path(__file__).resolve().parents[1] / "app.py",
    )
    app_module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(app_module)
    app_module.app.testing = True
    manager = app_module.GachaManager(app_module.get_save_manager())
    manager._set_items({"ticket": 1})
    return app_module.app, db_path


@pytest.mark.asyncio
async def test_pull_items(app_with_db):
    app, _ = app_with_db
    client = app.test_client()

    with patch(
        "autofighter.gacha.random.random", side_effect=[0.5, 1.0, 0.99]
    ), patch("autofighter.gacha.random.choice", return_value="fire"):
        resp = await client.post("/gacha/pull", json={"count": 1})
    data = await resp.get_json()
    assert data["pity"] == 1
    assert data["results"][0]["type"] == "item"
    assert data["results"][0]["rarity"] == 4
    assert data["items"]["fire_4"] == 1


@pytest.mark.asyncio
async def test_pull_requires_ticket(app_with_db):
    app, db_path = app_with_db
    conn = sqlcipher3.connect(db_path)
    conn.execute("PRAGMA key = 'testkey'")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS upgrade_items (id TEXT PRIMARY KEY, count INTEGER NOT NULL)"
    )
    conn.execute(
        "INSERT OR REPLACE INTO upgrade_items (id, count) VALUES (?, ?)",
        ("ticket", 0)
    )
    conn.commit()
    client = app.test_client()
    resp = await client.post("/gacha/pull", json={"count": 1})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_pull_five_star_duplicate(app_with_db):
    app, db_path = app_with_db
    client = app.test_client()

    with patch(
        "autofighter.gacha.random.random", side_effect=[0.5, 0.0]
    ), patch("autofighter.gacha.random.choice", return_value="becca"):
        resp = await client.post("/gacha/pull", json={"count": 1})
    data = await resp.get_json()
    assert data["pity"] == 0
    assert data["results"][0]["rarity"] == 5
    char_id = data["results"][0]["id"]

    from autofighter.gacha import FIVE_STAR

    conn = sqlcipher3.connect(db_path)
    conn.execute("PRAGMA key = 'testkey'")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS owned_players (id TEXT PRIMARY KEY)"
    )
    others = [cid for cid in FIVE_STAR if cid != char_id]
    for cid in others:
        conn.execute("INSERT OR IGNORE INTO owned_players (id) VALUES (?)", (cid,))
    conn.execute(
        "INSERT OR REPLACE INTO upgrade_items (id, count) VALUES (?, ?)",
        ("ticket", 1)
    )
    conn.commit()

    with patch(
        "autofighter.gacha.random.random", side_effect=[0.5, 0.0]
    ), patch("autofighter.gacha.random.choice", return_value=char_id):
        resp = await client.post("/gacha/pull", json={"count": 1})
    data = await resp.get_json()
    for player in data["players"]:
        if player["id"] == char_id:
            assert player["stacks"] == 2
            break
    else:
        pytest.fail("character not found")

    cur = conn.execute(
        "SELECT stacks FROM player_stacks WHERE id = ?", (char_id,)
    )
    assert cur.fetchone()[0] == 2


@pytest.mark.asyncio
async def test_pull_six_star(app_with_db):
    app, _ = app_with_db
    client = app.test_client()

    with patch(
        "autofighter.gacha.random.random", return_value=0.0
    ), patch(
        "autofighter.gacha.random.choice", return_value="lady_fire_and_ice"
    ):
        resp = await client.post("/gacha/pull", json={"count": 1})
    data = await resp.get_json()
    assert data["pity"] == 0
    assert data["results"][0]["rarity"] == 6
    assert data["results"][0]["id"] == "lady_fire_and_ice"



@pytest.mark.asyncio
async def test_pity_scales_item_rarity(app_with_db):
    app, db_path = app_with_db
    client = app.test_client()
    conn = sqlcipher3.connect(db_path)
    conn.execute("PRAGMA key = 'testkey'")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS options (key TEXT PRIMARY KEY, value TEXT)"
    )
    conn.execute(
        "INSERT OR REPLACE INTO options (key, value) VALUES ('gacha_pity', '178')"
    )
    conn.commit()
    with patch(
        "autofighter.gacha.random.random", side_effect=[0.5, 0.99, 0.05]
    ), patch("autofighter.gacha.random.choice", return_value="fire"):
        resp = await client.post("/gacha/pull", json={"count": 1})
    data = await resp.get_json()
    assert data["results"][0]["rarity"] >= 2


@pytest.mark.asyncio
async def test_expired_banners_pick_owned_and_unowned(app_with_db, monkeypatch):
    _, db_path = app_with_db

    import app as app_module

    manager = app_module.GachaManager(app_module.get_save_manager())

    from autofighter.gacha import FIVE_STAR, SIX_STAR

    featured_pool = list(dict.fromkeys([*FIVE_STAR, *SIX_STAR]))
    if len(featured_pool) < 2:
        pytest.skip("Insufficient featured characters for rotation test")

    owned_char = featured_pool[0]
    rotation_time = 1_000_000.0

    conn = sqlcipher3.connect(db_path)
    try:
        conn.execute("PRAGMA key = 'testkey'")
        conn.execute("CREATE TABLE IF NOT EXISTS owned_players (id TEXT PRIMARY KEY)")
        conn.execute("DELETE FROM owned_players")
        conn.execute("INSERT OR IGNORE INTO owned_players (id) VALUES (?)", (owned_char,))
        conn.execute(
            "UPDATE banners SET start_time = ?, end_time = ? WHERE banner_type = 'custom'",
            (rotation_time - 1000, rotation_time - 10),
        )
        conn.commit()
    finally:
        conn.close()

    monkeypatch.setattr("autofighter.gacha.time.time", lambda: rotation_time)
    monkeypatch.setattr("autofighter.gacha.random.choice", lambda seq: seq[0])

    manager._update_banner_rotation()

    owned_ids = manager._get_owned()
    custom_banners = [banner for banner in manager.get_banners() if banner.banner_type == "custom"]

    assert len(custom_banners) == 2
    featured_ids = [banner.featured_character for banner in custom_banners]
    assert len(set(featured_ids)) == len(featured_ids) or len(featured_ids) == 1

    owned_featured = sum(1 for cid in featured_ids if cid in owned_ids)
    unowned_featured = sum(1 for cid in featured_ids if cid not in owned_ids)

    assert owned_featured == 1
    assert unowned_featured == 1
