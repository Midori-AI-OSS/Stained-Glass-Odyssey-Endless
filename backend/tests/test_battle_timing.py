import time

import pytest

from autofighter.mapgen import MapNode
from autofighter.party import Party
from autofighter.rooms.battle.core import BattleRoom
from autofighter.stats import Stats


@pytest.mark.asyncio
async def test_per_actor_pacing():
    node = MapNode(room_id=0, room_type="battle-normal", floor=1, index=1, loop=1, pressure=0)
    room = BattleRoom(node)
    # Set stats so both sides act once before the foe is defeated
    player = Stats(hp=100)
    player.set_base_stat('max_hp', 100)
    player.set_base_stat('atk', 50)
    player.set_base_stat('defense', 0)
    player.id = "p1"
    foe = Stats(hp=100)
    foe.set_base_stat('max_hp', 100)
    foe.set_base_stat('atk', 50)
    foe.set_base_stat('defense', 0)
    foe.id = "f1"
    party = Party(members=[player])

    import autofighter.rooms.utils as rooms_module
    original = rooms_module._choose_foe
    rooms_module._choose_foe = lambda _party: foe
    start = time.perf_counter()
    await room.resolve(party, {})
    elapsed = time.perf_counter() - start
    rooms_module._choose_foe = original
    # Three total actions -> at least 1.5s of pacing (0.5s per action)
    assert elapsed >= 1.5
