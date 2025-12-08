from pathlib import Path
import sys

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))
from llms.loader import ModelName
from options import OptionKey
from options import set_option

from autofighter.rooms.battle import pacing as pacing_module


class FakeLLM:
    async def generate_stream(self, text: str):
        yield f"echo:{text}"


@pytest.fixture()
def app_with_db(tmp_path, monkeypatch):
    import importlib

    db_path = tmp_path / "save.db"
    monkeypatch.setenv("AF_DB_PATH", str(db_path))
    monkeypatch.setenv("AF_DB_KEY", "testkey")
    monkeypatch.syspath_prepend(Path(__file__).resolve().parents[1])

    # Force reload of options module to pick up the latest version
    if "options" in sys.modules:
        importlib.reload(sys.modules["options"])

    spec = importlib.util.spec_from_file_location(
        "app", Path(__file__).resolve().parents[1] / "app.py",
    )
    app_module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(app_module)
    app_module.app.testing = True
    return app_module.app


@pytest.mark.asyncio
async def test_lrm_config_endpoints(app_with_db, monkeypatch):
    app = app_with_db
    client = app.test_client()

    # Test GET endpoint returns expected fields
    resp = await client.get("/config/lrm")
    data = await resp.get_json()
    assert "current_model" in data
    assert "current_backend" in data
    assert "current_api_url" in data
    assert "current_api_key" in data
    assert "available_backends" in data
    assert "available_models" in data
    assert "auto" in data["available_backends"]
    assert "openai" in data["available_backends"]
    assert "huggingface" in data["available_backends"]
    assert ModelName.OPENAI_20B.value in data["available_models"]
    assert ModelName.OPENAI_120B.value in data["available_models"]

    # Test POST endpoint with model
    resp = await client.post("/config/lrm", json={"model": ModelName.OPENAI_120B.value})
    data = await resp.get_json()
    assert data["current_model"] == ModelName.OPENAI_120B.value
    assert "current_backend" in data
    assert "current_api_url" in data
    assert "current_api_key" in data

    # Test POST endpoint with backend
    resp = await client.post("/config/lrm", json={"backend": "openai"})
    data = await resp.get_json()
    assert data["current_backend"] == "openai"
    assert "current_model" in data
    assert "current_api_url" in data
    assert "current_api_key" in data

    # Test POST endpoint with API URL and key
    test_url = "http://localhost:11434/v1"
    test_key = "test-api-key-12345678"
    resp = await client.post("/config/lrm", json={"api_url": test_url, "api_key": test_key})
    data = await resp.get_json()
    assert data["current_api_url"] == test_url
    # API key should be masked
    assert data["current_api_key"] == "test...5678"

    # Test POST endpoint with both
    resp = await client.post("/config/lrm", json={"backend": "huggingface", "model": ModelName.OPENAI_20B.value})
    data = await resp.get_json()
    assert data["current_backend"] == "huggingface"
    assert data["current_model"] == ModelName.OPENAI_20B.value

    # Test backend-only endpoint
    resp = await client.post("/config/lrm/backend", json={"backend": "openai"})
    data = await resp.get_json()
    assert data["current_backend"] == "openai"

    # Test invalid backend
    resp = await client.post("/config/lrm/backend", json={"backend": "invalid"})
    assert resp.status_code == 400

    # Test test endpoint with fake loader
    calls = {}

    def fake_loader(model: str, validate: bool = True):
        calls["model"] = model
        return FakeLLM()

    monkeypatch.setattr("llms.loader.load_llm", fake_loader)
    resp = await client.post("/config/lrm/test", json={"prompt": "hi"})
    data = await resp.get_json()
    assert data["response"] == "echo:hi"
    # Just verify a model was passed to the loader
    assert "model" in calls


@pytest.mark.asyncio
async def test_turn_pacing_endpoints(app_with_db):
    app = app_with_db
    client = app.test_client()

    resp = await client.get("/config/turn_pacing")
    data = await resp.get_json()
    assert data["turn_pacing"] == pytest.approx(0.5)
    assert data["default"] == pytest.approx(0.5)
    assert data["default"] == pytest.approx(pacing_module.DEFAULT_TURN_PACING)

    resp = await client.post("/config/turn_pacing", json={"turn_pacing": 0.8})
    data = await resp.get_json()
    assert data["turn_pacing"] == pytest.approx(0.8)
    assert data["default"] == pytest.approx(0.5)
    assert pacing_module.TURN_PACING == pytest.approx(0.8)

    resp = await client.get("/config/turn_pacing")
    data = await resp.get_json()
    assert data["turn_pacing"] == pytest.approx(0.8)

    resp = await client.post("/config/turn_pacing", json={"turn_pacing": "NaN"})
    assert resp.status_code == 400
    assert pacing_module.TURN_PACING == pytest.approx(0.8)

    resp = await client.post("/config/turn_pacing", json={"turn_pacing": "Infinity"})
    assert resp.status_code == 400
    assert pacing_module.TURN_PACING == pytest.approx(0.8)

    resp = await client.post("/config/turn_pacing", json={"turn_pacing": -1})
    assert resp.status_code == 400

    set_option(OptionKey.TURN_PACING, "NaN")
    refreshed = pacing_module.refresh_turn_pacing()
    assert refreshed == pytest.approx(pacing_module.DEFAULT_TURN_PACING)
