from pathlib import Path
import random
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from autofighter.mapgen import MapNode
from autofighter.party import Party
from autofighter.rooms.utils import _choose_foe
from plugins.damage_types._base import DamageTypeBase
from plugins.characters import Player


def test_choose_foe_instantiates_damage_type() -> None:
    random.seed(0)
    party = Party(members=[Player()])
    node = MapNode(room_id=0, room_type="boss", floor=1, index=1, loop=1, pressure=0)
    foe = _choose_foe(node, party)
    assert isinstance(foe.damage_type, DamageTypeBase)
