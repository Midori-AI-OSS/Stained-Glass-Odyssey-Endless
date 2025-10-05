import pytest
from services.run_configuration import get_run_configuration_metadata
from services.run_configuration import validate_run_configuration


def test_run_configuration_metadata_shape():
    metadata = get_run_configuration_metadata()
    assert metadata["run_types"], "run types should be present"
    assert metadata["modifiers"], "modifiers should be present"
    pressure = metadata.get("pressure", {})
    assert "tooltip" in pressure and "encounter" in pressure["tooltip"].lower()


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
    assert pytest.approx(bonus, rel=1e-3) == 0.07
    assert selection.reward_bonuses["exp_bonus"] >= bonus


def test_validate_run_configuration_rejects_unknown_modifier():
    with pytest.raises(ValueError):
        validate_run_configuration(run_type="standard", modifiers={"invalid": 1})

