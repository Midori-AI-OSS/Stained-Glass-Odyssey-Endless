import asyncio

import pytest

from autofighter.stats import BUS
from autofighter.stats import Stats
from plugins.damage_types.fire import Fire


class Actor(Stats):
    async def use_ultimate(self) -> bool:
        if not self.ultimate_ready:
            return False
        self.ultimate_charge = 0
        self.ultimate_ready = False
        await BUS.emit_async("ultimate_used", self)
        return True


@pytest.mark.asyncio
async def test_fire_ultimate_stack_accumulation_and_drain():
    actor = Actor(damage_type=Fire())
    actor._base_defense = 0
    actor.id = "actor"
    actor.hp = actor.max_hp
    actor.ultimate_charge = 15
    actor.ultimate_ready = True
    await actor.use_ultimate()
    assert actor.damage_type._drain_stacks == 1

    BUS.emit("turn_start", actor)
    await asyncio.sleep(0)
    expected = actor.max_hp - int(actor.max_hp * 0.05)
    assert actor.hp == expected

    actor.ultimate_charge = 15
    actor.ultimate_ready = True
    await actor.use_ultimate()
    assert actor.damage_type._drain_stacks == 2

    BUS.emit("turn_start", actor)
    await asyncio.sleep(0)
    expected -= int(actor.max_hp * 0.10)
    assert actor.hp == expected

    BUS.emit("battle_end", actor)


@pytest.mark.asyncio
async def test_fire_ultimate_resets_on_battle_end():
    actor = Actor(damage_type=Fire())
    actor._base_defense = 0
    actor.id = "actor"
    actor.ultimate_charge = 15
    actor.ultimate_ready = True
    await actor.use_ultimate()
    assert actor.damage_type._drain_stacks == 1

    BUS.emit("battle_end", actor)
    assert actor.damage_type._drain_stacks == 0

    actor.hp = actor.max_hp
    BUS.emit("turn_start", actor)
    await asyncio.sleep(0)
    assert actor.hp == actor.max_hp


@pytest.mark.asyncio
async def test_fire_ultimate_damage_multiplier():
    attacker = Actor(damage_type=Fire())
    attacker._base_defense = 0
    attacker.id = "attacker"
    target = Stats()
    target._base_defense = 0
    target.id = "target"
    base = await target.apply_damage(100, attacker)

    attacker.ultimate_charge = 15
    attacker.ultimate_ready = True
    await attacker.use_ultimate()

    target2 = Stats()
    target2._base_defense = 0
    target2.id = "target2"
    boosted = await target2.apply_damage(100, attacker)
    assert boosted == base * 5

    BUS.emit("battle_end", attacker)
