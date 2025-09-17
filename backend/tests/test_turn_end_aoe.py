import copy
import random

import pytest

from autofighter.mapgen import MapNode
from autofighter.party import Party
from autofighter.rooms.battle.core import BattleRoom
from autofighter.stats import Stats
from plugins.damage_types.wind import Wind


@pytest.mark.asyncio
async def test_aoe_turn_end_advances_queue(monkeypatch):
    snapshots = []

    async def progress(snap):
        snapshots.append(copy.deepcopy(snap))

    node = MapNode(
        room_id=0,
        room_type="battle-normal",
        floor=1,
        index=1,
        loop=1,
        pressure=0,
    )
    room = BattleRoom(node)
    player = Stats(damage_type=Wind())
    player.id = "p1"
    player.set_base_stat("atk", 1000)
    foe1 = Stats(hp=3)
    foe1.set_base_stat("max_hp", 3)
    foe1.set_base_stat("defense", 0)
    foe1.id = "f1"
    foe2 = Stats(hp=3)
    foe2.set_base_stat("max_hp", 3)
    foe2.set_base_stat("defense", 0)
    foe2.id = "f2"
    party = Party(members=[player])

    random.seed(0)
    await room.resolve(party, {}, foe=[foe1, foe2], progress=progress)

    ended_snap = snapshots[-1]
    action_snaps = [s for s in snapshots if s.get("active_id") == "p1"]
    assert len(action_snaps) == 2
    first, second = action_snaps
    assert first.get("active_target_id") in {"f1", "f2"}
    assert second.get("active_target_id") is None
    assert first["action_queue"][0]["id"] == "p1"
    assert ended_snap.get("ended") is True
