import asyncio
import importlib.util
from pathlib import Path

import pytest

from plugins.damage_types.fire import Fire
from plugins.damage_types.ice import Ice
from plugins.foes._base import FoeBase


@pytest.fixture()
def app_with_db(tmp_path, monkeypatch):
    db_path = tmp_path / "save.db"
    monkeypatch.setenv("AF_DB_PATH", str(db_path))
    monkeypatch.setenv("AF_DB_KEY", "testkey")
    monkeypatch.syspath_prepend(Path(__file__).resolve().parents[1])
    spec = importlib.util.spec_from_file_location(
        "app",
        Path(__file__).resolve().parents[1] / "app.py",
    )
    app_module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(app_module)
    app_module.app.testing = True
    return app_module, db_path


@pytest.mark.asyncio
async def test_foe_element_stable_across_snapshots(app_with_db, monkeypatch):
    app_module, _ = app_with_db
    app = app_module.app
    client = app.test_client()

    elements = [Fire(), Ice()]

    class DummyFoe(FoeBase):
        id = "dummy"
        name = "Dummy"

    def choose_foe(_party):
        foe = DummyFoe()
        foe.damage_type = elements.pop(0)
        foe.hp = foe.max_hp = 1
        return foe

    import autofighter.rooms.utils as rooms_module

    monkeypatch.setattr(rooms_module, "_choose_foe", choose_foe)
    monkeypatch.setattr(app_module, "_scale_stats", lambda *args, **kwargs: None)
    monkeypatch.setattr(rooms_module, "_scale_stats", lambda *args, **kwargs: None)

    original_run_battle = app_module._run_battle

    async def delayed_run_battle(
        run_id, room, foes, party, data, state, rooms, progress
    ):
        await asyncio.sleep(0)
        return await original_run_battle(
            run_id, room, foes, party, data, state, rooms, progress
        )

    monkeypatch.setattr(app_module, "_run_battle", delayed_run_battle)

    start_resp = await client.post("/run/start", json={"party": ["player"]})
    run_id = (await start_resp.get_json())["run_id"]
    await client.put(f"/party/{run_id}", json={"party": ["player"]})

    battle_resp = await client.post(f"/rooms/{run_id}/battle")
    first = await battle_resp.get_json()
    initial = first["foes"][0]["element"]

    await asyncio.sleep(0)
    snap_resp = await client.post(
        f"/rooms/{run_id}/battle", json={"action": "snapshot"}
    )
    second = await snap_resp.get_json()

    assert second["foes"][0]["element"] == initial
