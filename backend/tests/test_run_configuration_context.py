import math

import pytest
from autofighter.stats import Stats
from services.run_configuration import RunModifierContext
from services.run_configuration import apply_player_modifier_context
from services.run_configuration import build_run_modifier_context
from services.run_configuration import get_modifier_snapshot
from services.run_configuration import get_room_overrides
from services.run_configuration import get_shop_modifier_summaries
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
    assert context.foe_strength_score >= 1.0
    assert context.foe_spawn_multiplier == pytest.approx(context.foe_strength_score)
    assert len(context.metadata_hash) == 64

    serialized = context.to_dict()
    assert serialized["metadata_hash"] == context.metadata_hash
    assert serialized["foe_stat_multipliers"]["max_hp"] == context.foe_stat_multipliers["max_hp"]
    assert serialized["foe_strength_score"] == pytest.approx(context.foe_strength_score)
    hydrated = RunModifierContext.from_dict(serialized)
    assert hydrated.shop_multiplier == pytest.approx(context.shop_multiplier)
    assert hydrated.encounter_slot_bonus == context.encounter_slot_bonus
    assert hydrated.foe_strength_score == pytest.approx(context.foe_strength_score)


def test_get_modifier_snapshot_normalises_entries():
    selection = validate_run_configuration(
        run_type="standard",
        modifiers={"pressure": 4, "foe_hp": 2},
    )
    snapshot = get_modifier_snapshot(selection.snapshot, "foe_hp")
    assert snapshot["stacks"] == 2
    assert snapshot["details"]["effective_bonus"] == selection.snapshot["modifiers"]["foe_hp"]["details"]["effective_bonus"]

    missing = get_modifier_snapshot(selection.snapshot, "nonexistent")
    assert missing["id"] == "nonexistent"
    assert missing["stacks"] == 0


def test_get_room_overrides_normalises_payload():
    selection = validate_run_configuration(run_type="standard", modifiers={"pressure": 0})
    selection.snapshot["room_overrides"] = {
        "shop": 0,
        "rest": {"enabled": True, "count": 2},
        "event": {"quantity": 1},
    }
    overrides = get_room_overrides(selection.snapshot)
    assert overrides["shop"]["enabled"] is False
    assert overrides["shop"]["count"] == 0
    assert overrides["rest"]["enabled"] is True
    assert overrides["rest"]["count"] == 2
    assert overrides["event"]["count"] == 1


def test_get_shop_modifier_summaries_filters_relevant_entries():
    selection = validate_run_configuration(run_type="standard", modifiers={"pressure": 3})
    selection.snapshot.setdefault("modifiers", {})["custom_shop"] = {
        "id": "custom_shop",
        "label": "Custom Shop",
        "category": "economy",
        "details": {
            "stacks": 2,
            "shop_multiplier": 1.1,
            "shop_tax_multiplier": 0.5,
            "shop_variance": (0.9, 1.2),
        },
    }

    summaries = get_shop_modifier_summaries(selection.snapshot)
    assert any(entry["id"] == "custom_shop" for entry in summaries)
    custom = next(entry for entry in summaries if entry["id"] == "custom_shop")
    assert custom["stacks"] == 2
    assert custom["details"]["shop_multiplier"] == pytest.approx(1.1)
    assert custom["details"]["shop_tax_multiplier"] == pytest.approx(0.5)
    assert custom["details"]["shop_variance"] == [0.9, 1.2]


def test_apply_player_modifier_context_scales_stats():
    selection = validate_run_configuration(
        run_type="standard",
        modifiers={"pressure": 0, "character_stat_down": 5},
    )
    context = build_run_modifier_context(selection.snapshot)

    member = Stats()
    baseline_hp = member.get_base_stat("max_hp")
    baseline_atk = member.get_base_stat("atk")

    multiplier = apply_player_modifier_context([member], context)

    expected_mult = context.player_stat_multiplier
    assert multiplier == pytest.approx(expected_mult)
    assert member.get_base_stat("max_hp") == pytest.approx(baseline_hp * expected_mult, abs=1)
    assert member.get_base_stat("atk") == pytest.approx(baseline_atk * expected_mult, abs=1)
    assert member.hp == member.max_hp
