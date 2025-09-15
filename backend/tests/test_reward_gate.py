import asyncio
import importlib.util
from pathlib import Path

import pytest


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
    return app_module.app


@pytest.mark.asyncio
async def test_advance_room_requires_reward_selection(app_with_db):
    from runs.lifecycle import load_map
    from runs.lifecycle import save_map

    app = app_with_db
    client = app.test_client()

    start_resp = await client.post("/run/start", json={"party": ["player"]})
    run_id = (await start_resp.get_json())["run_id"]

    # Simulate a battle that grants both card and relic rewards
    state, rooms = await asyncio.to_thread(load_map, run_id)
    state.update(
        {
            "awaiting_card": True,
            "awaiting_relic": True,
            "awaiting_loot": False,
            "awaiting_next": False,
            "reward_progression": {
                "available": ["card", "relic"],
                "completed": [],
                "current_step": "card",
            },
        }
    )
    await asyncio.to_thread(save_map, run_id, state)

    # Cannot advance while rewards are pending
    resp = await client.post("/ui/action", json={"action": "advance_room"})
    assert resp.status_code == 400

    # Selecting card still leaves relic to claim
    await client.post(
        "/ui/action",
        json={"action": "choose_card", "params": {"card_id": "micro_blade"}},
    )
    resp = await client.post("/ui/action", json={"action": "advance_room"})
    assert resp.status_code == 400

    # After choosing relic, advancing succeeds
    await client.post(
        "/ui/action",
        json={"action": "choose_relic", "params": {"relic_id": "threadbare_cloak"}},
    )
    resp = await client.post("/ui/action", json={"action": "advance_room"})
    data = await resp.get_json()
    assert resp.status_code == 200
    assert data.get("next_room") is not None
