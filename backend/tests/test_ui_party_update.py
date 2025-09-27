import asyncio
import importlib
import json
import math
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from quart import Quart
import sqlcipher3

importlib.invalidate_caches()
sys.modules.pop("services", None)
sys.modules.pop("tracking", None)
sys.modules.pop("battle_logging", None)
sys.modules.pop("battle_logging.writers", None)
from routes.ui import bp as ui_bp  # noqa: E402
from runs.lifecycle import load_map  # noqa: E402
from runs.lifecycle import save_map  # noqa: E402
from runs.party_manager import load_party  # noqa: E402
from runs.party_manager import save_party  # noqa: E402

from autofighter.mapgen import MapNode  # noqa: E402


@pytest.fixture()
def app_with_db(tmp_path, monkeypatch):
    db_path = tmp_path / "save.db"
    monkeypatch.setenv("AF_DB_PATH", str(db_path))
    monkeypatch.setenv("AF_DB_KEY", "testkey")
    monkeypatch.setenv("UV_EXTRA", "test")

    app = Quart(__name__)
    app.register_blueprint(ui_bp)
    app.testing = True
    return app, db_path


@pytest.mark.asyncio
async def test_update_party_success(app_with_db):
    app, db_path = app_with_db
    client = app.test_client()

    start_resp = await client.post("/run/start", json={"party": ["player"]})
    assert start_resp.status_code == 200

    conn = sqlcipher3.connect(db_path)
    conn.execute("PRAGMA key = 'testkey'")
    conn.execute("CREATE TABLE IF NOT EXISTS owned_players (id TEXT PRIMARY KEY)")
    conn.execute("INSERT OR IGNORE INTO owned_players (id) VALUES (?)", ("ally",))
    conn.commit()

    resp = await client.post(
        "/ui/action",
        json={"action": "update_party", "params": {"party": ["player", "ally"]}},
    )
    assert resp.status_code == 200
    data = await resp.get_json()
    assert data["party"]["members"] == ["player", "ally"]

    cur = conn.execute("SELECT party FROM runs")
    row = cur.fetchone()
    assert row is not None
    party_state = json.loads(row[0])
    assert party_state["members"] == ["player", "ally"]
    assert set(party_state["exp"]) == {"player", "ally"}
    assert set(party_state["level"]) == {"player", "ally"}


@pytest.mark.asyncio
async def test_update_party_missing_run(app_with_db):
    app, _ = app_with_db
    client = app.test_client()

    resp = await client.post(
        "/ui/action",
        json={
            "action": "update_party",
            "params": {"run_id": "missing", "party": ["player"]},
        },
    )
    assert resp.status_code == 404
    data = await resp.get_json()
    assert data["error"] == "Run not found"


@pytest.mark.asyncio
async def test_update_party_invalid_members(app_with_db):
    app, _ = app_with_db
    client = app.test_client()

    start_resp = await client.post("/run/start", json={"party": ["player"]})
    assert start_resp.status_code == 200

    duplicate_resp = await client.post(
        "/ui/action",
        json={
            "action": "update_party",
            "params": {"party": ["player", "player"]},
        },
    )
    assert duplicate_resp.status_code == 400
    duplicate_data = await duplicate_resp.get_json()
    assert duplicate_data["error"] == "invalid party"

    unowned_resp = await client.post(
        "/ui/action",
        json={
            "action": "update_party",
            "params": {"party": ["player", "becca"]},
        },
    )
    assert unowned_resp.status_code == 400
    unowned_data = await unowned_resp.get_json()
    assert unowned_data["error"] == "unowned character"


@pytest.mark.asyncio
async def test_shop_ui_state_persists(app_with_db):
    app, _ = app_with_db
    client = app.test_client()

    start_resp = await client.post("/run/start", json={"party": ["player"]})
    assert start_resp.status_code == 200
    start_payload = await start_resp.get_json()
    run_id = start_payload["run_id"]

    state, _ = await asyncio.to_thread(load_map, run_id)
    shop_node = MapNode(
        room_id=777,
        room_type="shop",
        floor=1,
        index=0,
        loop=1,
        pressure=2,
    )
    next_node = MapNode(
        room_id=778,
        room_type="battle-normal",
        floor=1,
        index=1,
        loop=1,
        pressure=2,
    )
    base_price = 100
    state.update(
        {
            "rooms": [shop_node.to_dict(), next_node.to_dict()],
            "current": 0,
            "battle": False,
            "awaiting_next": False,
            "awaiting_card": False,
            "awaiting_relic": False,
            "awaiting_loot": False,
            "shop_stock": {
                str(shop_node.room_id): [
                    {
                        "id": "shop_test_relic",
                        "name": "Shop Test Relic",
                        "stars": 2,
                        "type": "relic",
                        "base_price": base_price,
                        "price": base_price,
                        "cost": base_price,
                        "tax": 0,
                    }
                ]
            },
            "shop_items_bought": 1,
        }
    )
    await asyncio.to_thread(save_map, run_id, state)

    party = await asyncio.to_thread(load_party, run_id)
    party.gold = 200
    party.cards = []
    party.relics = []
    await asyncio.to_thread(save_party, run_id, party)

    first_resp = await client.get("/ui")
    assert first_resp.status_code == 200
    first_data = await first_resp.get_json()
    current_state = first_data["game_state"]["current_state"]
    room_data = current_state["room_data"]
    assert room_data["result"] == "shop"
    assert room_data["current_room"] == "shop"
    assert room_data["items_bought"] == 1
    assert room_data["gold"] == 200
    assert room_data["stock"]
    stock_entry = room_data["stock"][0]
    expected_tax = math.ceil(
        stock_entry["base_price"] * 0.01 * (shop_node.pressure + 1) * room_data["items_bought"]
    )
    assert stock_entry["tax"] == expected_tax
    assert stock_entry["cost"] == stock_entry["base_price"] + expected_tax

    second_resp = await client.get("/ui")
    assert second_resp.status_code == 200
    second_data = await second_resp.get_json()
    second_room = second_data["game_state"]["current_state"]["room_data"]
    assert second_room["stock"][0]["id"] == stock_entry["id"]
    assert second_room["items_bought"] == room_data["items_bought"]
    assert second_room["gold"] == room_data["gold"]

    purchase_resp = await client.post(
        "/ui/action",
        json={
            "action": "room_action",
            "params": {"id": stock_entry["id"], "cost": stock_entry["cost"]},
        },
    )
    assert purchase_resp.status_code == 200

    third_resp = await client.get("/ui")
    assert third_resp.status_code == 200
    third_data = await third_resp.get_json()
    third_room = third_data["game_state"]["current_state"]["room_data"]
    assert third_room["result"] == "shop"
    assert third_room["items_bought"] == room_data["items_bought"] + 1
    assert third_room["gold"] == room_data["gold"] - stock_entry["cost"]
    assert all(entry["id"] != stock_entry["id"] for entry in third_room["stock"])
