from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import random
import sys

import pytest

sys.path.append(str(Path(__file__).resolve().parents[3]))

from autofighter.mapgen import MapNode
from autofighter.rooms.foe_factory import ROOM_BALANCE_CONFIG
from autofighter.rooms.foe_factory import FoeFactory
from autofighter.rooms.foes.scaling import calculate_cumulative_rooms
from autofighter.rooms.foes.scaling import compute_base_multiplier
from autofighter.rooms.foes.scaling import enforce_thresholds
from autofighter.stats import Stats
from plugins.characters.foe_base import FoeBase


@dataclass
class DummyFoe(FoeBase):
    """Lightweight foe used for scaling helper tests."""

    def __post_init__(self) -> None:  # type: ignore[override]
        Stats.__post_init__(self)


def test_compute_base_multiplier_uses_growth_and_pressure() -> None:
    rng = random.Random(0)
    node = MapNode(
        room_id=3,
        room_type="battle-normal",
        floor=2,
        index=3,
        loop=2,
        pressure=4,
    )
    config = dict(ROOM_BALANCE_CONFIG)
    cumulative_rooms = calculate_cumulative_rooms(node)

    multiplier = compute_base_multiplier(
        1.2,
        node,
        config,
        cumulative_rooms=cumulative_rooms,
        rng=rng,
    )

    expected_rng = random.Random(0)
    variance = config["scaling_variance"]
    starter = 1.0 + expected_rng.uniform(-variance, variance)
    room_mult = starter + config["room_growth_multiplier"] * max(cumulative_rooms - 1, 0)
    loop_mult = starter + config["loop_growth_multiplier"] * max(node.loop - 1, 0)
    pressure_mult = config["pressure_multiplier"] * max(node.pressure, 1)
    expected = max(1.2 * room_mult * loop_mult * pressure_mult, 0.5)

    assert multiplier == pytest.approx(expected)


def test_enforce_thresholds_applies_pressure_defense_floor() -> None:
    rng = random.Random(0)
    node = MapNode(
        room_id=5,
        room_type="battle-hard",
        floor=3,
        index=4,
        loop=1,
        pressure=3,
    )
    config = dict(ROOM_BALANCE_CONFIG)
    foe = DummyFoe()
    foe.set_base_stat("defense", 1)
    cumulative_rooms = calculate_cumulative_rooms(node)

    enforce_thresholds(
        foe,
        node,
        config,
        cumulative_rooms=cumulative_rooms,
        foe_debuff=config["foe_base_debuff"],
        rng=rng,
    )

    expected_rng = random.Random(0)
    room_num = max(int(node.index), 1)
    base_hp = int(15 * room_num * config["foe_base_debuff"])
    low = int(base_hp * 0.85)
    high = int(base_hp * 1.10)
    expected_rng.randint(low, max(high, low + 1))
    base_def = node.pressure * config["pressure_defense_floor"]
    rand_factor = expected_rng.uniform(
        config["pressure_defense_min_roll"],
        config["pressure_defense_max_roll"],
    )
    pressure_defense = int(base_def * rand_factor)
    min_def = 2 + cumulative_rooms
    expected_defense = max(min_def, pressure_defense)

    assert foe.get_base_stat("defense") == expected_defense


def test_enforce_thresholds_clamps_vitality_and_mitigation() -> None:
    node = MapNode(
        room_id=1,
        room_type="battle-normal",
        floor=1,
        index=2,
        loop=1,
        pressure=0,
    )
    config = dict(ROOM_BALANCE_CONFIG)
    foe = DummyFoe()
    foe.set_base_stat("vitality", 2.0)
    foe.set_base_stat("mitigation", 0.5)

    enforce_thresholds(
        foe,
        node,
        config,
        cumulative_rooms=calculate_cumulative_rooms(node),
        foe_debuff=config["foe_base_debuff"],
    )

    vitality_excess = 2.0 - 0.5
    vitality_steps = int(vitality_excess // 0.25)
    expected_vitality = 0.5 + vitality_excess / (5.0 + vitality_steps)

    mitigation_excess = 0.5 - 0.2
    mitigation_steps = int(mitigation_excess // 0.01)
    expected_mitigation = 0.2 + mitigation_excess / (5.0 + mitigation_steps)

    assert foe.get_base_stat("vitality") == pytest.approx(expected_vitality)
    assert foe.get_base_stat("mitigation") == pytest.approx(expected_mitigation)


def test_scale_stats_retains_spawn_debuff_for_foe_base() -> None:
    config = dict(ROOM_BALANCE_CONFIG)
    config.update(
        {
            "scaling_variance": 0.0,
            "room_growth_multiplier": 0.0,
            "loop_growth_multiplier": 0.0,
            "pressure_multiplier": 1.0,
        }
    )
    factory = FoeFactory(config=config)
    node = MapNode(
        room_id=2,
        room_type="battle-normal",
        floor=1,
        index=1,
        loop=1,
        pressure=0,
    )
    foe = DummyFoe()

    base_hp = foe.get_base_stat("max_hp")
    base_atk = foe.get_base_stat("atk")
    base_defense = foe.get_base_stat("defense")

    factory.scale_stats(foe, node, strength=1.0)

    expected_hp = int(base_hp * config["foe_base_debuff"])
    expected_atk = int(base_atk * config["foe_base_debuff"])
    defense_multiplier = min((config["foe_base_debuff"] * node.floor) / 4, 1.0)
    expected_defense = int(base_defense * defense_multiplier)

    assert foe.get_base_stat("max_hp") == expected_hp
    assert foe.get_base_stat("atk") == expected_atk
    assert foe.get_base_stat("defense") == expected_defense
