import asyncio

import pytest

from autofighter.effects import EffectManager
from autofighter.stats import BUS
from autofighter.stats import Stats
from plugins.damage_types.wind import Wind
from plugins.dots.blazing_torment import BlazingTorment


async def _use_ultimate(self):
    if not getattr(self, "ultimate_ready", False):
        return False
    self.ultimate_charge = 0
    self.ultimate_ready = False
    await BUS.emit_async("ultimate_used", self)
    return True


@pytest.mark.asyncio
async def test_wind_ultimate_transfers_from_foes():
    Wind._players.clear()
    Wind._foes.clear()
    Wind._pending.clear()

    player = Stats(damage_type=Wind())
    player.plugin_type = "player"
    player.id = "p"
    foe1 = Stats()
    foe1.plugin_type = "foe"
    foe1._base_max_hp = 100
    foe1.hp = 100
    foe1._base_defense = 0
    foe1.id = "f1"
    foe2 = Stats()
    foe2.plugin_type = "foe"
    foe2._base_max_hp = 100
    foe2.hp = 100
    foe2._base_defense = 0
    foe2.id = "f2"
    foe1.effect_manager = EffectManager(foe1)
    foe2.effect_manager = EffectManager(foe2)

    dot = BlazingTorment(1, 3)
    dot.source = player
    foe2.effect_manager.add_dot(dot)

    player.use_ultimate = _use_ultimate.__get__(player, Stats)

    BUS.emit("battle_start", player)
    BUS.emit("battle_start", foe1)
    BUS.emit("battle_start", foe2)

    player.add_ultimate_charge(15)
    assert await player.use_ultimate()

    BUS.emit("hit_landed", player, foe1, 0, "attack")
    await asyncio.sleep(0.01)

    assert foe2.effect_manager.dots == []
    assert foe2.dots == []
    assert foe1.hp == 99

    BUS.emit("battle_end", player)
    BUS.emit("battle_end", foe1)
    BUS.emit("battle_end", foe2)


@pytest.mark.asyncio
async def test_wind_foe_ultimate_transfers_from_allies():
    Wind._players.clear()
    Wind._foes.clear()
    Wind._pending.clear()

    foe = Stats(damage_type=Wind())
    foe.plugin_type = "foe"
    foe.id = "f"
    p1 = Stats()
    p1.plugin_type = "player"
    p1._base_max_hp = 100
    p1.hp = 100
    p1._base_defense = 0
    p1.id = "p1"
    p2 = Stats()
    p2.plugin_type = "player"
    p2._base_max_hp = 100
    p2.hp = 100
    p2._base_defense = 0
    p2.id = "p2"
    p1.effect_manager = EffectManager(p1)
    p2.effect_manager = EffectManager(p2)

    dot = BlazingTorment(1, 3)
    dot.source = foe
    p2.effect_manager.add_dot(dot)

    foe.use_ultimate = _use_ultimate.__get__(foe, Stats)

    BUS.emit("battle_start", foe)
    BUS.emit("battle_start", p1)
    BUS.emit("battle_start", p2)

    foe.add_ultimate_charge(15)
    assert await foe.use_ultimate()

    BUS.emit("hit_landed", foe, p1, 0, "attack")
    await asyncio.sleep(0.01)

    assert p2.effect_manager.dots == []
    assert p2.dots == []
    assert p1.hp == 99

    BUS.emit("battle_end", foe)
    BUS.emit("battle_end", p1)
    BUS.emit("battle_end", p2)
