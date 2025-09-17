import pytest

from autofighter.mapgen import MapNode
from autofighter.party import Party
from autofighter.rooms.battle.core import BattleRoom
from autofighter.stats import Stats
from plugins.players.player import Player


@pytest.mark.asyncio
async def test_battle_end_on_all_foes_dead():
    player = Player()
    party = Party(members=[player])
    node = MapNode(0, "battle-normal", 1, 0, 1, 0)
    room = BattleRoom(node=node)
    foe = Stats()
    foe.id = "dummy"
    foe.hp = 1
    result = await room.resolve(party, {}, foe=foe)
    assert result["ended"] is True
