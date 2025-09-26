import pytest

from autofighter import rooms
from autofighter.mapgen import MapNode
from autofighter.party import Party
from plugins.characters.foe_base import FoeBase
from plugins.characters._base import PlayerBase


@pytest.mark.asyncio
async def test_enrage_stacks(monkeypatch):
    class DummyFoe(FoeBase):
        id = "dummy-foe"
        hp = 5
        max_hp = 5
        atk = 5
        defense = 1000

    class DummyPlayer(PlayerBase):
        id = "dummy-player"
        hp = 5
        max_hp = 5
        atk = 5
        defense = 1000

    monkeypatch.setattr(
        "autofighter.rooms.battle.setup._build_foes",
        lambda node, party, **kwargs: [DummyFoe()],
    )
    monkeypatch.setattr(rooms, "ENRAGE_TURNS_NORMAL", 2)

    node = MapNode(room_id=0, room_type="battle-normal", floor=1, index=1, loop=1, pressure=0)
    party = Party(members=[DummyPlayer()])

    room = rooms.BattleRoom(node)
    result = await room.resolve(party, {})

    assert result["enrage"]["active"] is True
    assert result["enrage"]["stacks"] == 3
    foe = result["foes"][0]
    assert foe["atk"] == 11
    assert any(p["id"] == "Enraged" for p in foe["passives"])
