from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # noqa: E402

import pytest

from autofighter.mapgen import MapNode
from autofighter.party import Party
from autofighter.rooms import utils
from plugins.players import Player


def _make_party(size: int) -> Party:
    return Party(members=[Player() for _ in range(size)])


def _make_node(pressure: int) -> MapNode:
    return MapNode(
        room_id=0,
        room_type="battle-boss-floor",
        floor=1,
        index=1,
        loop=1,
        pressure=pressure,
    )


@pytest.mark.parametrize("size,pressure", [(1, 0), (3, 10), (5, 50)])
def test_boss_rooms_spawn_one_foe(size: int, pressure: int) -> None:
    party = _make_party(size)
    node = _make_node(pressure)
    foes = utils._build_foes(node, party)
    assert len(foes) == 1
    assert foes[0].rank == "boss"
