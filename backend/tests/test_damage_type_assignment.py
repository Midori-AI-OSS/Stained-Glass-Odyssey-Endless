import random

import pytest

from autofighter.mapgen import MapNode
from autofighter.party import Party
from autofighter.rooms.battle.core import BattleRoom
from plugins.damage_types._base import DamageTypeBase
from plugins.foes._base import FoeBase
from plugins.foes.slime import Slime
from plugins.players._base import PlayerBase
from plugins.players.carly import Carly


def test_base_classes_assign_damage_type() -> None:
    random.seed(0)
    player = PlayerBase()
    foe = FoeBase()
    assert isinstance(player.damage_type, DamageTypeBase)
    assert isinstance(foe.damage_type, DamageTypeBase)


def test_plugin_overrides_damage_type() -> None:
    carly = Carly()
    assert carly.damage_type.id == "Light"


@pytest.mark.asyncio
async def test_battle_uses_preset_damage_types() -> None:
    node = MapNode(
        room_id=0,
        room_type="battle-normal",
        floor=1,
        index=1,
        loop=1,
        pressure=0,
    )
    room = BattleRoom(node)
    player = Carly()
    foe = Slime()
    party = Party(members=[player])
    await room.resolve(party, {}, foe=foe)
    assert player.damage_type.id == "Light"
    assert isinstance(foe.damage_type, DamageTypeBase)
