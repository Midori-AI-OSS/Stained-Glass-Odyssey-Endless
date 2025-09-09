import pytest
from test_app import app_with_db as _app_with_db  # reuse fixture  # noqa: F401


@pytest.mark.asyncio
async def test_party_save_and_validation(app_with_db):
    app, _ = app_with_db
    client = app.test_client()
    start_resp = await client.post("/run/start", json={"party": ["player"]})
    run_id = (await start_resp.get_json())["run_id"]

    good = await client.put(f"/party/{run_id}", json={"party": ["player"]})
    assert good.status_code == 200

    map_resp = await client.get(f"/map/{run_id}")
    map_data = await map_resp.get_json()
    assert map_data["party"] == ["player"]

    bad = await client.put(f"/party/{run_id}", json={"party": ["player", "evil"]})
    assert bad.status_code == 400
    bad_data = await bad.get_json()
    assert bad_data["error"] == "unowned character"
