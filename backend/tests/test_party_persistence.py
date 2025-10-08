import pytest
from runs.party_manager import load_party
from services.run_configuration import build_run_modifier_context
from services.run_configuration import validate_run_configuration
from services.user_level_service import get_user_level
from test_app import app_with_db  # noqa: F401

from plugins.characters import player as player_module


@pytest.mark.asyncio
async def test_party_save_and_validation(app_with_db):
    app, _ = app_with_db
    client = app.test_client()
    start_resp = await client.post('/run/start', json={'party': ['player']})
    run_id = (await start_resp.get_json())['run_id']

    good = await client.put(f'/party/{run_id}', json={'party': ['player']})
    assert good.status_code == 200

    map_resp = await client.get(f'/map/{run_id}')
    map_data = await map_resp.get_json()
    assert map_data['party'] == ['player']

    bad = await client.put(f'/party/{run_id}', json={'party': ['player', 'evil']})
    assert bad.status_code == 400
    bad_data = await bad.get_json()
    assert bad_data['error'] == 'unowned character'


@pytest.mark.asyncio
async def test_load_party_applies_run_modifier_context(app_with_db):
    app, _ = app_with_db
    client = app.test_client()

    stacks = 5
    start_resp = await client.post(
        '/run/start',
        json={'party': ['player'], 'modifiers': {'character_stat_down': stacks}},
    )
    payload = await start_resp.get_json()
    run_id = payload['run_id']

    party = load_party(run_id)
    loaded_player = next(member for member in party.members if member.id == 'player')

    baseline_player = player_module.Player()
    selection = validate_run_configuration(
        run_type='standard',
        modifiers={'character_stat_down': stacks},
    )
    context = build_run_modifier_context(selection.snapshot)
    multiplier = context.player_stat_multiplier
    user_level = get_user_level()
    user_level_multiplier = 1.0 + float(user_level) * 0.01

    expected_hp = int(round(baseline_player.get_base_stat('max_hp') * user_level_multiplier * multiplier))
    expected_atk = int(round(baseline_player.get_base_stat('atk') * user_level_multiplier * multiplier))

    assert loaded_player.get_base_stat('max_hp') == expected_hp
    assert loaded_player.get_base_stat('atk') == expected_atk
