import random

from autofighter.mapgen import MapNode
from autofighter.rooms.utils import _scale_stats
from plugins.foes.slime import Slime


def test_slime_scaling_uses_reduced_base_stats() -> None:
    random.seed(0)

    slime = Slime()

    assert slime.max_hp == 100
    assert slime.atk == 10
    assert slime.defense == 5

    assert slime.get_base_stat("max_hp") == 100
    assert slime.get_base_stat("atk") == 10
    assert slime.get_base_stat("defense") == 5

    node = MapNode(
        room_id=1,
        room_type="battle-normal",
        floor=1,
        index=1,
        loop=1,
        pressure=0,
    )

    _scale_stats(slime, node)

    assert slime.max_hp == 50
    assert slime.atk == 5
    assert slime.defense == 0
