import asyncio
from datetime import datetime
from datetime import timedelta
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
    assert data["daily_rdr_bonus"] == pytest.approx(0.0)
    expected_types = {dtype.lower() for dtype in login_rewards.ALL_DAMAGE_TYPES}
    for item in data["reward_items"]:
        assert item["stars"] >= 1
        assert item["item_id"].endswith(str(item["stars"]))
        assert item["damage_type"] in expected_types
        assert isinstance(item["name"], str) and item["name"]

    second = await client.get("/rewards/login")
    second_data = await second.get_json()
    assert second_data["reward_items"] == data["reward_items"]
    assert second_data["daily_rdr_bonus"] == pytest.approx(data["daily_rdr_bonus"])


@pytest.mark.asyncio
async def test_login_reward_auto_claim_flow(app_with_db):
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
    assert status["rooms_completed"] >= 3
    assert status["claimed_today"] is True
    assert status["can_claim"] is False
    assert "daily_rdr_bonus" in status

    manager = login_rewards.GachaManager(login_rewards.get_save_manager())

    def get_inventory() -> dict[str, int]:
        return manager._get_items()

    inventory = await asyncio.to_thread(get_inventory)
    assert inventory
    for entry in status["reward_items"]:
        key = entry["item_id"]
        assert inventory.get(key, 0) >= 1

    # Claiming again on the same day should fail
    second = await client.post("/rewards/login/claim")
    assert second.status_code == 400
    error = await second.get_json()
    assert error["error"] == "reward already claimed"

    refreshed = await client.get("/rewards/login")
    refreshed_data = await refreshed.get_json()
    assert refreshed_data["claimed_today"] is True
    assert refreshed_data["can_claim"] is False


@pytest.mark.asyncio
async def test_daily_rdr_bonus_progression_and_reset():
    await _initialize_state()

    base_time = datetime(2024, 1, 1, 9, tzinfo=PT)
    status = await login_rewards.get_login_reward_status(now=base_time)
    assert status["daily_rdr_bonus"] == pytest.approx(0.0)

    for offset in range(login_rewards.ROOMS_REQUIRED + 2):
        await login_rewards.record_room_completion(now=base_time + timedelta(minutes=offset + 1))

    updated = await login_rewards.get_login_reward_status(now=base_time + timedelta(hours=1))
    expected_bonus = login_rewards._calculate_daily_rdr_bonus(updated["rooms_completed"], updated["streak"])
    assert expected_bonus < 1.0
    assert updated["daily_rdr_bonus"] == pytest.approx(expected_bonus)

    bonus_accessor = await login_rewards.get_daily_rdr_bonus(now=base_time + timedelta(hours=2))
    assert bonus_accessor == pytest.approx(updated["daily_rdr_bonus"])

    next_day = await login_rewards.get_login_reward_status(now=base_time + timedelta(days=1))
    assert next_day["daily_rdr_bonus"] == pytest.approx(0.0)
    accessor_reset = await login_rewards.get_daily_rdr_bonus(now=base_time + timedelta(days=1, hours=1))
    assert accessor_reset == pytest.approx(0.0)
    assert next_day["rooms_completed"] == 0


@pytest.mark.parametrize(
    ("extra_rooms", "streak", "expected"),
    [
        (0, 1, 0.0),
        (110, 100, 1.01),
        (115, 100, 1.015),
        (116, 100, 1.0151),
        (130, 100, 1.0165),
        (150, 100, 1.016655),
    ],
)
def test_calculate_daily_rdr_bonus_diminishing(extra_rooms, streak, expected):
    rooms_completed = login_rewards.ROOMS_REQUIRED + extra_rooms
    bonus = login_rewards._calculate_daily_rdr_bonus(rooms_completed, streak)
    assert bonus == pytest.approx(expected)


@pytest.mark.asyncio
async def test_party_load_applies_daily_bonus_and_resets(app_with_db):
    app, _ = app_with_db

    await _initialize_state()

    current_time = datetime.now(tz=PT)
    await login_rewards.get_login_reward_status(now=current_time)

    start = await start_run(["player"])
    run_id = start["run_id"]

    from runs.party_manager import load_party as load_party_sync
    from runs.party_manager import save_party as save_party_sync

    initial_party = load_party_sync(run_id)
    base_rdr = getattr(initial_party, "base_rdr", initial_party.rdr)

    for offset in range(login_rewards.ROOMS_REQUIRED + 2):
        await login_rewards.record_room_completion(
            now=current_time + timedelta(minutes=offset + 1)
        )

    status = await login_rewards.get_login_reward_status(
        now=current_time + timedelta(hours=1)
    )
    daily_bonus = status["daily_rdr_bonus"]
    assert daily_bonus > 0.0

    boosted_party = load_party_sync(run_id)
    assert getattr(boosted_party, "login_rdr_bonus", None) == pytest.approx(daily_bonus)
    assert boosted_party.rdr == pytest.approx(base_rdr + daily_bonus)

    save_party_sync(run_id, boosted_party)

    await login_rewards.get_login_reward_status(now=current_time + timedelta(days=1))

    reset_party = load_party_sync(run_id)
    assert getattr(reset_party, "login_rdr_bonus", None) == pytest.approx(0.0)
    assert reset_party.rdr == pytest.approx(base_rdr)
