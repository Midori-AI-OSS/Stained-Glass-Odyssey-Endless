import importlib.util
from pathlib import Path
import sys
import types

sys.modules.setdefault("llms.torch_checker", types.SimpleNamespace(is_torch_available=lambda: False))

from autofighter.mapgen import MapNode  # noqa: E402
from autofighter.party import Party  # noqa: E402
from plugins.players import Player  # noqa: E402

sys.modules.setdefault("autofighter.rooms", types.ModuleType("autofighter.rooms"))

spec = importlib.util.spec_from_file_location(
    "autofighter.rooms.utils",
    Path(__file__).resolve().parents[1] / "autofighter/rooms/utils.py",
)
room_utils = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(room_utils)
_build_foes = room_utils._build_foes
_serialize = room_utils._serialize


def test_normal_foe_rank() -> None:
    party = Party(members=[Player()])
    node = MapNode(
        room_id=0,
        room_type="battle-normal",
        floor=1,
        index=1,
        loop=1,
        pressure=0,
    )
    foes = _build_foes(node, party, [])
    data = [_serialize(f) for f in foes]
    assert all(f["rank"] == "normal" for f in data)


def test_boss_foe_rank() -> None:
    party = Party(members=[Player()])
    node = MapNode(
        room_id=0,
        room_type="battle-boss-floor",
        floor=1,
        index=1,
        loop=1,
        pressure=0,
    )
    foes = _build_foes(node, party, [])
    data = [_serialize(f) for f in foes]
    assert data[0]["rank"] == "boss"
