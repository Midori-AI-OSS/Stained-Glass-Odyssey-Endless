from pathlib import Path
import shutil

from battle_logging.writers import BattleLogger
import pytest

from autofighter.stats import BUS
from autofighter.stats import Stats


@pytest.mark.asyncio
async def test_battle_summary_endpoint(app_with_db):
    app, _ = app_with_db
    run_id = "summary_run"
    logger = BattleLogger(run_id, 1)

    attacker = Stats()
    attacker.id = "hero"
    attacker.damage_type = type("dt", (), {"id": "Fire"})()
    target = Stats()
    target.id = "foe"

    await BUS.emit_async("damage_dealt", attacker, target, 42, damage_type="Fire")
    logger.finalize_battle("victory")

    client = app.test_client()

    try:
        overview = await client.get(f"/logs/{run_id}")
        assert overview.status_code == 200
        overview_data = await overview.get_json()
        assert overview_data["run_id"] == run_id
        assert overview_data["battle_count"] == 1
        assert overview_data["battles"][0]["summary"]["result"] == "victory"

        summary_resp = await client.get(f"/logs/{run_id}/battles/1/summary")
        assert summary_resp.status_code == 200
        summary_data = await summary_resp.get_json()
        assert summary_data["damage_by_type"]["hero"]["Fire"] == 42

        events_resp = await client.get(f"/logs/{run_id}/battles/1/events")
        assert events_resp.status_code == 200
        events_data = await events_resp.get_json()
        assert any(event["event_type"] == "damage_dealt" for event in events_data)
    finally:
        logs_root = Path(__file__).resolve().parents[1] / "logs" / "runs" / run_id
        if logs_root.exists():
            shutil.rmtree(logs_root)
        legacy_root = Path(__file__).resolve().parents[1] / "battle_logging" / "logs" / "runs" / run_id
        if legacy_root.exists():
            shutil.rmtree(legacy_root)
