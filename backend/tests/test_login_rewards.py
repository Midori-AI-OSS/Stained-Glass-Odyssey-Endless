import asyncio
from datetime import datetime
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from services import login_reward_service as login_rewards
from services.run_service import advance_room
from services.run_service import start_run

PT = ZoneInfo("America/Los_Angeles")


pytest_plugins = ("tests.test_app",)


async def _initialize_state():
    manager = login_rewards.get_save_manager()

    def reset_state() -> None:
        with manager.connection() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS options (key TEXT PRIMARY KEY, value TEXT)"
            )
            conn.execute(
                "DELETE FROM options WHERE key = ?",
                (login_rewards.STATE_KEY,),
            )

    await asyncio.to_thread(reset_state)
    await login_rewards.get_login_reward_status(now=datetime(2024, 1, 1, 9, tzinfo=PT))


@pytest.mark.asyncio
async def test_login_reward_status_endpoint(app_with_db):
    app, _ = app_with_db
    client = app.test_client()

    await _initialize_state()

    resp = await client.get("/rewards/login")
    assert resp.status_code == 200
    data = await resp.get_json()
    assert data["streak"] == 1
    assert data["rooms_completed"] == 0
    assert data["rooms_required"] == 3
    assert data["claimed_today"] is False
    assert data["can_claim"] is False
    assert data["seconds_until_reset"] > 0
    assert data["reward_items"]
    expected_types = {dtype.lower() for dtype in login_rewards.ALL_DAMAGE_TYPES}
    for item in data["reward_items"]:
        assert item["stars"] >= 1
        assert item["item_id"].endswith(str(item["stars"]))
        assert item["damage_type"] in expected_types
        assert isinstance(item["name"], str) and item["name"]

    second = await client.get("/rewards/login")
    second_data = await second.get_json()
    assert second_data["reward_items"] == data["reward_items"]


@pytest.mark.asyncio
async def test_login_reward_claim_flow(app_with_db):
    app, _ = app_with_db
    client = app.test_client()

    await _initialize_state()

    start = await start_run(["player"])
    run_id = start["run_id"]

    # Advance three rooms to meet the requirement
    await advance_room(run_id)
    await advance_room(run_id)
    await advance_room(run_id)

    status_resp = await client.get("/rewards/login")
    status = await status_resp.get_json()
    assert status["can_claim"] is True
    assert status["rooms_completed"] >= 3

    claim_resp = await client.post("/rewards/login/claim")
    assert claim_resp.status_code == 200
    claim = await claim_resp.get_json()
    assert claim["streak"] == status["streak"]
    assert claim["reward_items"] == status["reward_items"]
    assert claim["inventory"]
    for entry in claim["reward_items"]:
        key = entry["item_id"]
        assert claim["inventory"][key] >= 1

    # Claiming again on the same day should fail
    second = await client.post("/rewards/login/claim")
    assert second.status_code == 400
    error = await second.get_json()
    assert error["error"] == "reward already claimed"

    refreshed = await client.get("/rewards/login")
    refreshed_data = await refreshed.get_json()
    assert refreshed_data["claimed_today"] is True
    assert refreshed_data["can_claim"] is False
