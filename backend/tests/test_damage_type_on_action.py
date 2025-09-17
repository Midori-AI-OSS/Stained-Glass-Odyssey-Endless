import pytest

from autofighter.mapgen import MapNode
from autofighter.party import Party
from autofighter.rooms.battle.core import BattleRoom
from autofighter.stats import Stats
from plugins.damage_types._base import DamageTypeBase


class CancelDamage(DamageTypeBase):
    id = "Cancel"

    async def on_action(self, actor, allies, enemies):
        return False


@pytest.mark.asyncio
async def test_player_damage_type_cancels_attack():
    node = MapNode(
        room_id=0,
        room_type="battle-normal",
        floor=1,
        index=1,
        loop=1,
        pressure=0,
    )
    room = BattleRoom(node)
    player = Stats(hp=10, damage_type=CancelDamage())
    player.set_base_stat('max_hp', 10)
    player.set_base_stat('defense', 0)
    player.set_base_stat('atk', 5)
    player.id = "p1"
    foe = Stats(hp=10)
    foe.set_base_stat('max_hp', 10)
    foe.set_base_stat('atk', 1000)
    foe.set_base_stat('defense', 0)
    foe.id = "f1"
    party = Party(members=[player])
    await room.resolve(party, {}, foe=foe)
    assert foe.hp == foe.max_hp


@pytest.mark.asyncio
async def test_foe_damage_type_cancels_attack():
    node = MapNode(
        room_id=0,
        room_type="battle-normal",
        floor=1,
        index=1,
        loop=1,
        pressure=0,
    )
    room = BattleRoom(node)
    player = Stats()
    player.set_base_stat('atk', 1000)
    player.set_base_stat('defense', 0)
    player.id = "p1"
    foe = Stats(hp=10, damage_type=CancelDamage())
    foe.set_base_stat('max_hp', 10)
    foe.set_base_stat('atk', 5)
    foe.set_base_stat('defense', 0)
    foe.id = "f1"
    party = Party(members=[player])
    await room.resolve(party, {}, foe=foe)
    assert player.hp == player.max_hp
