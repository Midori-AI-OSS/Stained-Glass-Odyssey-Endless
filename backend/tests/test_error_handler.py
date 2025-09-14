import importlib.util
from pathlib import Path
import sys

import pytest


@pytest.fixture()
def app_client(tmp_path, monkeypatch):
    db_path = tmp_path / "save.db"
    monkeypatch.setenv("AF_DB_PATH", str(db_path))
    monkeypatch.setenv("AF_DB_KEY", "testkey")
    if "game" in sys.modules:
        del sys.modules["game"]
    monkeypatch.syspath_prepend(Path(__file__).resolve().parents[1])
    spec = importlib.util.spec_from_file_location(
        "app", Path(__file__).resolve().parents[1] / "app.py",
    )
    app_module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(app_module)
    app_module.app.testing = True

    called = {"flag": False}

    async def fake_shutdown() -> None:
        called["flag"] = True

    monkeypatch.setattr(app_module, "request_shutdown", fake_shutdown)

    @app_module.app.route("/explode")
    async def explode() -> None:
        raise RuntimeError("boom")

    return app_module.app.test_client(), called


@pytest.mark.asyncio
async def test_error_handler_returns_traceback(app_client):
    client, called = app_client
    response = await client.get("/explode")
    assert response.status_code == 500
    data = await response.get_json()
    assert "traceback" in data
    assert "RuntimeError" in data["traceback"]
    assert response.headers["Access-Control-Allow-Origin"] == "*"
    assert called["flag"] is True


@pytest.mark.asyncio
async def test_http_exception_does_not_shutdown(app_client):
    client, called = app_client
    response = await client.get("/missing")
    assert response.status_code == 404
    data = await response.get_json()
    assert "traceback" not in data
    assert called["flag"] is False
