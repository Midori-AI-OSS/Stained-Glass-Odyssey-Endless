import asyncio
import importlib.util
from pathlib import Path

import pytest

from autofighter.rooms import BattleRoom


@pytest.fixture()
def app_with_shutdown(tmp_path, monkeypatch):
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
    return app_module


@pytest.mark.asyncio
async def test_battle_error_triggers_shutdown(app_with_shutdown, monkeypatch):
    app_module = app_with_shutdown
    app = app_module.app
    client = app.test_client()

    async def boom(self, party, data, progress, foe=None):
        raise RuntimeError("boom")

    monkeypatch.setattr(BattleRoom, "resolve", boom)

    loop = asyncio.get_running_loop()

    def stop() -> None:
        raise SystemExit

    monkeypatch.setattr(loop, "stop", stop)

    start_resp = await client.post("/run/start", json={"party": ["player"]})
    run_id = (await start_resp.get_json())["run_id"]

    await client.post(f"/rooms/{run_id}/battle")
    task = app_module.battle_tasks[run_id]

    with pytest.raises(SystemExit):
        await task
