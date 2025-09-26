import importlib.util
from pathlib import Path
import random
import sys
import types

import pytest

sys.modules.setdefault("llms.torch_checker", types.SimpleNamespace(is_torch_available=lambda: False))

from autofighter.mapgen import MapNode
from autofighter.party import Party
from plugins.characters import Player

spec = importlib.util.spec_from_file_location(
    "autofighter.rooms.utils",
    Path(__file__).resolve().parents[1] / "autofighter/rooms/utils.py",
)
assert spec.loader is not None
utils = importlib.util.module_from_spec(spec)
spec.loader.exec_module(utils)


def _make_party(size: int = 1) -> Party:
    return Party(members=[Player() for _ in range(size)])


def _make_node(room_type: str = "battle-normal", pressure: int = 0) -> MapNode:
    return MapNode(
        room_id=0,
        room_type=room_type,
        floor=1,
        index=1,
        loop=1,
        pressure=pressure,
    )


def test_rank_probability_progression_scaling() -> None:
    base = utils.calculate_rank_probabilities(0, 0, 0)
    assert base == (0.0, 0.0)

    mid = utils.calculate_rank_probabilities(500, 1, 0)
    assert mid == pytest.approx((0.001, 0.001))

    pressure_boost = utils.calculate_rank_probabilities(100, 0, 2)
    assert pressure_boost == pytest.approx((0.0201, 0.0201))

    capped = utils.calculate_rank_probabilities(2_000_000, 3, 10)
    assert capped == (1.0, 1.0)


def test_build_foes_prime_with_seed(monkeypatch) -> None:
    party = _make_party()
    node = _make_node(pressure=0)
    progression = {
        "total_rooms_cleared": 2_000,
        "floors_cleared": 1,
        "current_pressure": 1,
    }

    rng = random.Random(15)
    monkeypatch.setattr(utils, "random", rng)

    foes = utils._build_foes(node, party, progression=progression)
    assert foes
    assert foes[0].rank == "prime"


def test_build_foes_glitched_with_seed(monkeypatch) -> None:
    party = _make_party()
    node = _make_node(pressure=0)
    progression = {
        "total_rooms_cleared": 2_000,
        "floors_cleared": 1,
        "current_pressure": 1,
    }

    rng = random.Random(71)
    monkeypatch.setattr(utils, "random", rng)

    foes = utils._build_foes(node, party, progression=progression)
    assert foes
    assert foes[0].rank == "glitched"


def test_build_foes_glitched_prime_high_progression(monkeypatch) -> None:
    party = _make_party(3)
    node = _make_node(pressure=0)
    progression = {
        "total_rooms_cleared": 1_000_000,
        "floors_cleared": 5,
        "current_pressure": 10,
    }

    rng = random.Random(123)
    monkeypatch.setattr(utils, "random", rng)

    foes = utils._build_foes(node, party, progression=progression)
    assert foes
    assert all(foe.rank == "glitched prime" for foe in foes)
