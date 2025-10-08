import importlib
import importlib.util
from pathlib import Path
import sys
import types

import pytest


@pytest.fixture()
def app_with_db(tmp_path, monkeypatch):
    db_path = tmp_path / "save.db"
    monkeypatch.setenv("AF_DB_PATH", str(db_path))
    monkeypatch.setenv("AF_DB_KEY", "testkey")
    monkeypatch.syspath_prepend(Path(__file__).resolve().parents[1])
    sys.modules.pop("services", None)
    sys.modules.pop("services.asset_service", None)
    asset_service_module = importlib.import_module("services.asset_service")
    class _TrackingStub:
        def __getattr__(self, _name):
            return lambda *args, **kwargs: None

    tracking_stub = _TrackingStub()
    monkeypatch.setitem(sys.modules, "tracking", tracking_stub)
    battle_logging_writers = types.SimpleNamespace(
        end_run_logging=lambda *a, **k: None,
        end_battle_logging=lambda *a, **k: None,
        BattleLogger=type(
            "BattleLogger",
            (),
            {
                "__init__": lambda self, *a, **k: None,
                "start": lambda self, *a, **k: None,
                "stop": lambda self, *a, **k: None,
            },
        ),
        start_battle_logging=lambda *a, **k: None,
        get_current_run_logger=lambda: None,
    )
    battle_logging_stub = types.SimpleNamespace(writers=battle_logging_writers)
    monkeypatch.setitem(sys.modules, "battle_logging", battle_logging_stub)
    monkeypatch.setitem(sys.modules, "battle_logging.writers", battle_logging_writers)
    options_stub = types.SimpleNamespace(
        OptionKey=str,
        get_option=lambda *_args, default=None, **_kwargs: default,
        set_option=lambda *a, **k: None,
    )
    monkeypatch.setitem(sys.modules, "options", options_stub)
    user_level_stub = types.SimpleNamespace(
        get_user_state=lambda: {},
        get_user_level=lambda *a, **k: 1,
        gain_user_exp=lambda *a, **k: None,
    )
    login_reward_stub = types.SimpleNamespace(
        claim_login_reward=lambda *a, **k: {},
        get_login_reward_status=lambda: {},
    )
    reward_service_stub = types.SimpleNamespace(
        acknowledge_loot=lambda *a, **k: {},
        select_card=lambda *a, **k: {},
        select_relic=lambda *a, **k: {},
    )
    room_service_stub = types.SimpleNamespace(
        room_action=lambda *a, **k: {},
        advance_room=lambda *a, **k: {},
    )
    class _RunServiceStub:
        def __getattr__(self, _name):
            return lambda *args, **kwargs: {}

    run_service_stub = _RunServiceStub()
    services_module = types.ModuleType("services")
    services_module.user_level_service = user_level_stub
    services_module.login_reward_service = login_reward_stub
    services_module.reward_service = reward_service_stub
    services_module.room_service = room_service_stub
    services_module.run_service = run_service_stub
    services_module.asset_service = asset_service_module
    monkeypatch.setitem(sys.modules, "services", services_module)
    monkeypatch.setitem(sys.modules, "services.user_level_service", user_level_stub)
    monkeypatch.setitem(sys.modules, "services.login_reward_service", login_reward_stub)
    monkeypatch.setitem(sys.modules, "services.reward_service", reward_service_stub)
    monkeypatch.setitem(sys.modules, "services.room_service", room_service_stub)
    monkeypatch.setitem(sys.modules, "services.run_service", run_service_stub)
    monkeypatch.setitem(sys.modules, "services.asset_service", asset_service_module)
    torch_checker = types.SimpleNamespace(
        is_torch_available=lambda: False,
        get_torch_import_error=lambda: None,
        require_torch=lambda: None,
    )
    llms_module = types.SimpleNamespace(torch_checker=torch_checker)
    monkeypatch.setitem(sys.modules, "llms", llms_module)
    monkeypatch.setitem(sys.modules, "llms.torch_checker", torch_checker)
    spec = importlib.util.spec_from_file_location(
        "app", Path(__file__).resolve().parents[1] / "app.py"
    )
    app_module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(app_module)
    app_module.app.testing = True
    return app_module.app, db_path


@pytest.mark.asyncio
async def test_players_expose_ui_metadata(app_with_db):
    app, _ = app_with_db
    client = app.test_client()
    response = await client.get("/players")
    data = await response.get_json()

    roster = {entry["id"]: entry for entry in data.get("players", [])}

    assert "mimic" in roster
    assert "lady_echo" in roster

    mimic_meta = roster["mimic"].get("ui") or {}
    assert mimic_meta.get("non_selectable") is True
    assert mimic_meta.get("portrait_pool") == "player_mirror"

    echo_meta = roster["lady_echo"].get("ui") or {}
    assert echo_meta.get("portrait_pool") == "player_gallery"
    assert echo_meta.get("non_selectable") is not True


@pytest.mark.asyncio
async def test_ui_bootstrap_includes_asset_manifest(app_with_db):
    app, _ = app_with_db
    client = app.test_client()

    response = await client.get("/ui")
    assert response.status_code == 200

    payload = await response.get_json()
    manifest = payload.get("asset_manifest")

    assert isinstance(manifest, dict)

    portraits = {entry["id"]: entry for entry in manifest.get("portraits", []) if isinstance(entry, dict) and entry.get("id")}
    assert "echo" in portraits
    assert "mimic" in portraits

    echo_entry = portraits["echo"]
    assert "lady_echo" in (echo_entry.get("aliases") or [])

    mimic_entry = portraits["mimic"]
    mimic_descriptor = mimic_entry.get("mimic") or {}
    assert mimic_descriptor.get("mode") == "player_mirror"
    assert mimic_descriptor.get("target") == "player"

    summons = {entry["id"]: entry for entry in manifest.get("summons", []) if isinstance(entry, dict) and entry.get("id")}
    assert "jellyfish" in summons
    jellyfish_entry = summons["jellyfish"]
    aliases = jellyfish_entry.get("aliases") or []
    assert "jellyfish_electric" in aliases
    assert jellyfish_entry.get("portrait") is True
