from pathlib import Path
import random
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from autofighter.mapgen import MapNode
from autofighter.party import Party
from autofighter.rooms.utils import _choose_foe
from plugins import characters
from plugins import themedadj
from plugins.characters import Player


def test_random_player_foes() -> None:
    random.seed(0)
    party = Party(members=[Player()])
    player_ids = {
        getattr(characters, name).id
        for name in getattr(characters, "__all__", [])
        if hasattr(getattr(characters, name), "id")
    }
    node = MapNode(room_id=0, room_type="boss", floor=1, index=1, loop=1, pressure=0)
    seen = [_choose_foe(node, party) for _ in range(20)]
    ids = {foe.id for foe in seen}
    assert any(fid in player_ids and fid != "slime" for fid in ids)
    player_foes = [foe for foe in seen if foe.id != "slime"]
    if player_foes:
        foe_name = player_foes[0].name
        assert any(adj.title() in foe_name for adj in themedadj.__all__)
