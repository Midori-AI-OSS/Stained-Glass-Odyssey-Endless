import math

import pytest
from services.run_configuration import RunModifierContext
from services.run_configuration import build_run_modifier_context
from services.run_configuration import validate_run_configuration


def test_build_run_modifier_context_matches_snapshot_metadata():
    selection = validate_run_configuration(
        run_type="standard",
        modifiers={
            "pressure": 7,
            "foe_hp": 3,
            "foe_mitigation": 2,
            "foe_glitched_rate": 4,
            "foe_prime_rate": 1,
            "character_stat_down": 5,
        },
    )

    context = build_run_modifier_context(selection.snapshot)

    assert context.pressure == 7
    assert math.isclose(context.shop_multiplier, 1.26 ** 7, rel_tol=1e-9)
    assert context.shop_tax_multiplier == pytest.approx(1.0)
    assert context.shop_variance == (0.95, 1.05)
    hp_effect = selection.snapshot["modifiers"]["foe_hp"]["details"]["effective_bonus"]
    assert context.foe_stat_multipliers["max_hp"] == pytest.approx(1.0 + hp_effect)
    mitigation_effect = selection.snapshot["modifiers"]["foe_mitigation"]["details"]["effective_bonus"]
    assert context.foe_stat_deltas["mitigation"] == pytest.approx(mitigation_effect)
    glitched_bonus = selection.snapshot["modifiers"]["foe_glitched_rate"]["details"]["raw_bonus"] * 100.0
    assert context.glitched_spawn_bonus_pct == pytest.approx(glitched_bonus)
    prime_bonus = selection.snapshot["modifiers"]["foe_prime_rate"]["details"]["raw_bonus"] * 100.0
    assert context.prime_spawn_bonus_pct == pytest.approx(prime_bonus)
    player_multiplier = selection.snapshot["modifiers"]["character_stat_down"]["details"]["effective_multiplier"]
    assert context.player_stat_multiplier == pytest.approx(player_multiplier)
    assert context.encounter_slot_bonus == 1
    assert context.pressure_defense_floor == pytest.approx(70.0)
    assert context.pressure_defense_min_roll == pytest.approx(0.82)
    assert context.pressure_defense_max_roll == pytest.approx(1.50)
    assert context.modifier_stacks["foe_hp"] == 3
    assert len(context.metadata_hash) == 64

    serialized = context.to_dict()
    assert serialized["metadata_hash"] == context.metadata_hash
    assert serialized["foe_stat_multipliers"]["max_hp"] == context.foe_stat_multipliers["max_hp"]
    hydrated = RunModifierContext.from_dict(serialized)
    assert hydrated.shop_multiplier == pytest.approx(context.shop_multiplier)
    assert hydrated.encounter_slot_bonus == context.encounter_slot_bonus
