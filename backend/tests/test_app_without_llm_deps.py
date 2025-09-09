import builtins
import importlib.util
from pathlib import Path

import pytest


@pytest.fixture()
def app_without_llm(tmp_path, monkeypatch):
    db_path = tmp_path / "save.db"
    monkeypatch.setenv("AF_DB_PATH", str(db_path))
    monkeypatch.setenv("AF_DB_KEY", "testkey")

    original_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "torch":
            raise ImportError("No module named 'torch'")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    monkeypatch.syspath_prepend(Path(__file__).resolve().parents[1])
    spec = importlib.util.spec_from_file_location(
        "app",
        Path(__file__).resolve().parents[1] / "app.py",
    )
    app_module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(app_module)
    app_module.app.testing = True
    return app_module.app


@pytest.mark.asyncio
async def test_non_llm_endpoints_work_without_deps(app_without_llm):
    app = app_without_llm
    client = app.test_client()

    status_resp = await client.get("/")
    assert status_resp.status_code == 200

    config_resp = await client.get("/config/lrm")
    assert config_resp.status_code == 200
    data = await config_resp.get_json()
    assert "available_models" in data

    players_resp = await client.get("/players")
    assert players_resp.status_code == 200
