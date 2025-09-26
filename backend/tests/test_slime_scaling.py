from pathlib import Path
import random
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))

import battle_logging  # noqa: F401  # Ensure package is importable for foe factory side effects

from autofighter.effects import calculate_diminishing_returns
from autofighter.mapgen import MapNode
from autofighter.rooms.foe_factory import FoeFactory
from autofighter.rooms.foes.scaling import apply_permanent_scaling
from autofighter.rooms.utils import _scale_stats
from autofighter.stats import Stats
from plugins.foes import PLAYER_FOES
from plugins.players.slime import Slime


def test_slime_player_uses_default_base_stats() -> None:
    random.seed(0)

    slime = Slime()

    assert slime.max_hp == 1000
    assert slime.atk == 100
    assert slime.defense == 50

    assert slime.get_base_stat("max_hp") == 1000
    assert slime.get_base_stat("atk") == 100
    assert slime.get_base_stat("defense") == 50

    node = MapNode(
        room_id=1,
        room_type="battle-normal",
        floor=1,
        index=1,
        loop=1,
        pressure=0,
    )

    _scale_stats(slime, node)

    assert slime.max_hp >= 1000
    assert slime.atk >= 100
    assert slime.defense >= 0
    assert not hasattr(slime, "_pending_mods")


def test_slime_room_scaling_respects_player_baseline(monkeypatch) -> None:
    random.seed(0)

    monkeypatch.setattr("plugins.foes.ADJ_CLASSES", [], raising=False)

    slime_cls = PLAYER_FOES[Slime.id]
    slime = slime_cls()

    baseline_hp = slime.base_max_hp
    baseline_atk = slime.base_atk
    baseline_def = slime.base_defense

    assert slime.max_hp == baseline_hp
    assert slime.atk == baseline_atk
    assert slime.defense == baseline_def

    node = MapNode(
        room_id=1,
        room_type="battle-normal",
        floor=1,
        index=1,
        loop=1,
        pressure=0,
    )

    factory = FoeFactory()
    factory.scale_stats(slime, node)

    assert slime.max_hp > 0
    assert slime.atk > 0
    assert slime.defense >= 0

    assert slime.max_hp >= baseline_hp
    assert slime.atk >= baseline_atk
    assert slime.get_base_stat("atk") >= baseline_atk
    assert slime.get_base_stat("defense") >= baseline_def


def test_apply_permanent_scaling_skips_unknown_stats() -> None:
    stats = Stats()

    result = apply_permanent_scaling(
        stats,
        multipliers={"nonexistent": 2.0},
        name="Unknown stat",
        modifier_id="test_unknown_stat",
    )

    assert result == {}
    assert not hasattr(stats, "_pending_mods")


def test_apply_permanent_scaling_updates_base_stats() -> None:
    stats = Stats()

    outcome = apply_permanent_scaling(
        stats,
        multipliers={"atk": 0.5},
        deltas={"max_hp": -100},
        name="half_atk",
        modifier_id="test_half_atk",
    )

    assert stats.atk == 100
    assert stats.get_base_stat("atk") == 100
    assert stats.max_hp == 900
    assert stats.get_base_stat("max_hp") == 900
    assert outcome == {"atk": -100.0, "max_hp": -100.0}
    assert not hasattr(stats, "_pending_mods")


def test_apply_permanent_scaling_respects_diminishing_returns() -> None:
    stats = Stats()
    stats.set_base_stat("atk", 2000)

    initial_base = stats.get_base_stat("atk")
    initial_current = stats.atk
    raw_delta = initial_base * (2.0 - 1.0)
    scaling_factor = calculate_diminishing_returns("atk", initial_current)

    assert scaling_factor < 1.0

    outcome = apply_permanent_scaling(
        stats,
        multipliers={"atk": 2.0},
        name="diminished_atk",
        modifier_id="test_diminished_atk",
    )

    expected_base = type(initial_base)(initial_base + raw_delta * scaling_factor)

    assert stats.get_base_stat("atk") == expected_base
    assert stats.atk == expected_base
    assert outcome == {"atk": expected_base - initial_base}
