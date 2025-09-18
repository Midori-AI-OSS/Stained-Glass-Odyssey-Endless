from pathlib import Path
import sys
from typing import Iterator

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # noqa: E402

from autofighter.mapgen import MapNode
from autofighter.party import Party
from autofighter.rooms import utils
from plugins.players import Player


class DummyFoe:
    id = "dummy"
    name = "Dummy"


def _make_party(size: int) -> Party:
    return Party(members=[Player() for _ in range(size)])


def _make_node() -> MapNode:
    return MapNode(room_id=0, room_type="battle", floor=1, index=1, loop=1, pressure=0)


def _run(monkeypatch, values: list[float]) -> int:
    it: Iterator[float] = iter(values)
    monkeypatch.setattr(utils, "_choose_foe", lambda party: DummyFoe())
    monkeypatch.setattr(utils.random, "random", lambda: next(it, 1.0))
    party = _make_party(3)
    node = _make_node()
    return len(utils._build_foes(node, party, []))


def test_add_two_foes(monkeypatch) -> None:
    assert _run(monkeypatch, [0.1]) == 3


def test_add_one_foe(monkeypatch) -> None:
    assert _run(monkeypatch, [0.4, 0.5]) == 2


def test_add_no_foes(monkeypatch) -> None:
    assert _run(monkeypatch, [0.4, 0.9]) == 1
