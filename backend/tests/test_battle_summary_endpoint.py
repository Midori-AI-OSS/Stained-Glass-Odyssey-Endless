from battle_logging.writers import BattleLogger
import pytest

from autofighter.stats import BUS
from autofighter.stats import Stats


@pytest.mark.asyncio
async def test_battle_summary_endpoint(app_with_db):
    app, _ = app_with_db
    run_id = 'summary_run'
    logger = BattleLogger(run_id, 1)

    attacker = Stats()
    attacker.id = 'hero'
    attacker.damage_type = type('dt', (), {'id': 'Fire'})()
    target = Stats()
    target.id = 'foe'

    await BUS.emit_async('damage_dealt', attacker, target, 42, damage_type='Fire')
    logger.finalize_battle('victory')

    client = app.test_client()
    resp = await client.get(f'/run/{run_id}/battles/1/summary')
    assert resp.status_code == 200
    data = await resp.get_json()
    assert data['damage_by_type']['hero']['Fire'] == 42
