import pytest
from services.run_configuration import get_run_configuration_metadata
from services.run_configuration import validate_run_configuration
from services.run_service import start_run
from test_app import app_with_db as _app_with_db  # reuse database-backed app fixture

app_with_db = _app_with_db


def test_run_configuration_metadata_shape():
    metadata = get_run_configuration_metadata()
    assert metadata["run_types"], "run types should be present"
    assert metadata["modifiers"], "modifiers should be present"
    pressure = metadata.get("pressure", {})
    assert "tooltip" in pressure and "encounter" in pressure["tooltip"].lower()


def test_run_configuration_metadata_details():
    metadata = get_run_configuration_metadata()
    foe_hp = next(mod for mod in metadata["modifiers"] if mod["id"] == "foe_hp")
    assert foe_hp["effects"]["per_stack"] == pytest.approx(0.5)
    assert foe_hp["diminishing_returns"]["applies"] is True
    preview_five = next(item for item in foe_hp["preview"] if item["stacks"] == 5)
    assert preview_five["raw_bonus"] == pytest.approx(2.5)
    foe_speed = next(mod for mod in metadata["modifiers"] if mod["id"] == "foe_speed")
    assert foe_speed["reward_bonuses"]["exp_bonus_per_stack"] == pytest.approx(0.5)
    pressure = next(mod for mod in metadata["modifiers"] if mod["id"] == "pressure")
    assert "encounter_bonus" in pressure["effects"]
    pressure_preview = next(item for item in pressure["preview"] if item["stacks"] == 10)
    assert pressure_preview["encounter_bonus"] == 2


def test_validate_run_configuration_defaults():
    selection = validate_run_configuration(run_type=None, modifiers=None, fallback_pressure=4)
    assert selection.run_type["id"] == "standard"
    assert selection.pressure == 4
    assert selection.reward_bonuses["exp_multiplier"] >= 1.0
    assert selection.snapshot["pressure"]["tooltip"]


def test_validate_run_configuration_with_modifiers():
    selection = validate_run_configuration(
        run_type="boss_rush",
        modifiers={"foe_hp": 4, "character_stat_down": 3},
    )
    assert selection.modifiers["pressure"] >= 5
    bonus = selection.snapshot["modifiers"]["character_stat_down"]["details"]["bonus_rdr"]
    assert pytest.approx(bonus, rel=1e-3) == 0.17
    assert selection.reward_bonuses["exp_bonus"] >= bonus


def test_validate_run_configuration_rejects_unknown_modifier():
    with pytest.raises(ValueError):
        validate_run_configuration(run_type="standard", modifiers={"invalid": 1})


@pytest.mark.asyncio
async def test_start_run_persists_configuration_snapshot(app_with_db):
    app, _ = app_with_db
    _ = app  # ensure fixture is exercised to initialise database
    result = await start_run(
        ["player"],
        run_type="boss_rush",
        modifiers={"foe_mitigation": 2, "character_stat_down": 2},
    )
    config = result["configuration"]
    assert config["run_type"]["id"] == "boss_rush"
    char_penalty = config["modifiers"]["character_stat_down"]["details"]
    assert pytest.approx(char_penalty["bonus_rdr"], rel=1e-3) == 0.11
    assert pytest.approx(config["reward_bonuses"]["exp_bonus"], rel=1e-3) == 2.11


@pytest.mark.asyncio
async def test_start_run_rejects_invalid_modifier_values(app_with_db):
    app, _ = app_with_db
    _ = app
    with pytest.raises(ValueError):
        await start_run(["player"], modifiers={"pressure": -1})

