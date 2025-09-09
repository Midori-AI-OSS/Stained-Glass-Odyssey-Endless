from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


@pytest.fixture
def app_with_db(tmp_path, monkeypatch):
    db_path = tmp_path / "save.db"
    monkeypatch.setenv("AF_DB_PATH", str(db_path))
    monkeypatch.setenv("AF_DB_KEY", "testkey")
    monkeypatch.setenv("UV_EXTRA", "test")
    if "game" in list(__import__("sys").modules):
        del __import__("sys").modules["game"]
    spec = importlib.util.spec_from_file_location(
        "app",
        Path(__file__).resolve().parents[1] / "app.py",
    )
    app_module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(app_module)
    app_module.app.testing = True
    return app_module.app, db_path


@pytest.mark.asyncio
async def test_damage_types_endpoint(app_with_db):
    app, _ = app_with_db
    client = app.test_client()
    resp = await client.get("/guidebook/damage-types")
    assert resp.status_code == 200
    data = await resp.get_json()
    assert "damage_types" in data
    assert isinstance(data["damage_types"], list)
    assert any("id" in d and "weakness" in d for d in data["damage_types"])


@pytest.mark.asyncio
async def test_passives_endpoint(app_with_db):
    app, _ = app_with_db
    client = app.test_client()
    resp = await client.get("/guidebook/passives")
    assert resp.status_code == 200
    data = await resp.get_json()
    assert "passives" in data
    assert isinstance(data["passives"], list)
    if data["passives"]:
        p = data["passives"][0]
        assert "id" in p
        assert "name" in p


@pytest.mark.asyncio
async def test_shops_and_ui_mechs_endpoints(app_with_db):
    app, _ = app_with_db
    client = app.test_client()
    shops = await (await client.get("/guidebook/shops")).get_json()
    assert "reroll_cost" in shops and "price_by_stars" in shops
    ui = await (await client.get("/guidebook/ui")).get_json()
    assert "tips" in ui and isinstance(ui["tips"], list)
    mechs = await (await client.get("/guidebook/mechs")).get_json()
    assert "mechanics" in mechs and isinstance(mechs["mechanics"], list)


@pytest.mark.asyncio
async def test_stats_endpoint(app_with_db):
    app, _ = app_with_db
    client = app.test_client()
    resp = await client.get("/guidebook/stats")
    assert resp.status_code == 200
    data = await resp.get_json()
    assert "stats" in data
    assert "level_info" in data
    assert "common_passives" in data
    assert isinstance(data["stats"], list)

    # Verify we have all expected stats
    stat_names = [stat["name"] for stat in data["stats"]]
    expected_stats = [
        "Health Points (HP)",
        "Attack (ATK)",
        "Defense (DEF)",
        "Critical Rate",
        "Critical Damage",
        "Vitality",
        "Effect Hit Rate",
        "Effect Resistance",
        "Dodge Rate",
        "Mitigation",
    ]
    for expected in expected_stats:
        assert expected in stat_names


@pytest.mark.asyncio
async def test_effects_endpoint(app_with_db):
    app, _ = app_with_db
    client = app.test_client()
    resp = await client.get("/guidebook/effects")
    assert resp.status_code == 200
    data = await resp.get_json()
    assert "combat_effects" in data
    assert "dot_effects" in data
    assert "categories" in data
    assert isinstance(data["combat_effects"], list)
    assert isinstance(data["dot_effects"], list)


@pytest.mark.asyncio
async def test_ultimates_endpoint(app_with_db):
    app, _ = app_with_db
    client = app.test_client()
    resp = await client.get("/guidebook/ultimates")
    assert resp.status_code == 200
    data = await resp.get_json()
    assert "ultimates" in data
    assert isinstance(data["ultimates"], list)

    # Verify Generic type is included
    ultimate_ids = [ult["id"] for ult in data["ultimates"]]
    assert "Generic" in ultimate_ids
