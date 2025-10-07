import importlib.util
import json
from pathlib import Path
import sys

import pytest
import sqlcipher3


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
        "app", Path(__file__).resolve().parents[1] / "app.py",
    )
    app_module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(app_module)
    app_module.app.testing = True
    return app_module.app, db_path


@pytest.mark.asyncio
async def test_status_endpoint(app_with_db):
    app, _ = app_with_db
    client = app.test_client()
    response = await client.get("/")
    assert response.status_code == 200
    data = await response.get_json()
    assert data == {"status": "ok", "flavor": "test"}


@pytest.mark.asyncio
async def test_run_flow(app_with_db):
    app, db_path = app_with_db
    client = app.test_client()

    start_resp = await client.post("/run/start", json={"party": ["player"]})
    start_data = await start_resp.get_json()
    run_id = start_data["run_id"]

    await client.put(f"/party/{run_id}", json={"party": ["player"]})

    map_resp = await client.get(f"/map/{run_id}")
    map_data = await map_resp.get_json()
    assert map_data["map"]["current"] == 1
    assert len(map_data["map"]["rooms"]) == 10
    assert map_data["map"]["battle"] is False

    conn = sqlcipher3.connect(db_path)
    conn.execute("PRAGMA key = 'testkey'")
    cur = conn.execute("SELECT party FROM runs WHERE id = ?", (run_id,))
    row = cur.fetchone()
    party_data = json.loads(row[0])
    assert party_data["members"] == ["player"]
    assert party_data["gold"] == 0
    assert party_data["relics"] == []


@pytest.mark.asyncio
async def test_players_and_rooms(app_with_db):
    app, _ = app_with_db
    client = app.test_client()

    players_resp = await client.get("/players")
    players_data = await players_resp.get_json()
    player_entry = next(p for p in players_data["players"] if p["id"] == "player")
    assert player_entry["owned"]
    assert player_entry["element"] == "Fire"
    assert player_entry["stats"]["hp"] == 1000

    start_resp = await client.post("/run/start", json={"party": ["player"]})
    run_id = (await start_resp.get_json())["run_id"]

    await client.put(f"/party/{run_id}", json={"party": ["player"]})

    async def advance_until(predicate):
        while True:
            map_resp = await client.get(f"/map/{run_id}")
            state = (await map_resp.get_json())["map"]
            node = state["rooms"][state["current"]]
            rt = node["room_type"]
            endpoint = {
                "battle-weak": "battle",
                "battle-normal": "battle",
                "battle-prime": "battle",
                "battle-glitched": "battle",
                "battle-boss-floor": "boss",
                "shop": "shop",
            }[rt]
            url = f"/rooms/{run_id}/{endpoint}"
            if rt == "shop":
                resp = await client.post(url, json={"cost": 1, "item": "potion"})
            else:
                resp = await client.post(url)
            await client.post(f"/run/{run_id}/next")
            if predicate(rt):
                return resp

    battle_resp = await advance_until(
        lambda rt: rt in {"battle-weak", "battle-normal", "battle-prime", "battle-glitched"}
    )
    assert battle_resp.status_code == 200
    battle_data = await battle_resp.get_json()
    assert "foes" in battle_data
    foe = battle_data["foes"][0]
    assert foe["id"] != "player"
    assert "atk" in foe
    assert "rank" in foe

    map_state = (await (await client.get(f"/map/{run_id}")).get_json())["map"]
    assert map_state["battle"] is False
    assert "defense" in foe
    assert "atk" in battle_data["party"][0]

    shop_resp = await advance_until(lambda rt: rt == "shop")
    assert shop_resp.status_code == 200
    shop_data = await shop_resp.get_json()
    assert "party" in shop_data


@pytest.mark.asyncio
async def test_room_images(app_with_db):
    app, _ = app_with_db
    client = app.test_client()

    resp = await client.get("/rooms/images")
    data = await resp.get_json()
    assert resp.status_code == 200
    assert {
        "battle-weak",
        "battle-normal",
        "battle-prime",
        "battle-glitched",
        "battle-boss-floor",
        "shop",
    } <= data["images"].keys()
