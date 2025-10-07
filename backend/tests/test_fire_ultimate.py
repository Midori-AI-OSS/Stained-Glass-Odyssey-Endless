import asyncio
import random
import types

import pytest

from autofighter.stats import BUS
from autofighter.stats import Stats
from autofighter.stats import set_battle_active
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
    actor.ultimate_charge = actor.ultimate_charge_max
    actor.ultimate_ready = True
    await actor.use_ultimate()
    assert actor.damage_type._drain_stacks == 1

    set_battle_active(True)
    try:
        await BUS.emit_async("turn_start", actor)
        await asyncio.sleep(0.01)
    finally:
        set_battle_active(False)
    expected = actor.max_hp - int(actor.max_hp * 0.05)
    assert actor.hp == expected

    actor.ultimate_charge = actor.ultimate_charge_max
    actor.ultimate_ready = True
    await actor.use_ultimate()
    assert actor.damage_type._drain_stacks == 2

    set_battle_active(True)
    try:
        await BUS.emit_async("turn_start", actor)
        await asyncio.sleep(0.01)
    finally:
        set_battle_active(False)
    expected -= int(actor.max_hp * 0.10)
    assert actor.hp == expected

    await BUS.emit_async("battle_end", actor)


@pytest.mark.asyncio
async def test_fire_ultimate_resets_on_battle_end():
    actor = Actor(damage_type=Fire())
    actor._base_defense = 0
    actor.id = "actor"
    actor.ultimate_charge = actor.ultimate_charge_max
    actor.ultimate_ready = True
    await actor.use_ultimate()
    assert actor.damage_type._drain_stacks == 1

    await BUS.emit_async("battle_end", actor)
    assert actor.damage_type._drain_stacks == 0

    actor.hp = actor.max_hp
    await BUS.emit_async("turn_start", actor)
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

    attacker.ultimate_charge = attacker.ultimate_charge_max
    attacker.ultimate_ready = True
    await attacker.use_ultimate()

    target2 = Stats()
    target2._base_defense = 0
    target2.id = "target2"
    boosted = await target2.apply_damage(100, attacker)
    assert boosted == base * 5

    await BUS.emit_async("battle_end", attacker)


@pytest.mark.asyncio
async def test_fire_ultimate_prefers_high_aggro_targets():
    random.seed(42)

    actor = Actor(damage_type=Fire())
    actor.id = "fire-actor"
    actor.atk = 90
    actor.ultimate_charge = actor.ultimate_charge_max
    actor.ultimate_ready = True

    foes: list[Stats] = []
    hits: dict[str, int] = {}

    async def record_damage(self, *_args, **_kwargs):
        hits[self.id] = hits.get(self.id, 0) + 1
        return 0

    for idx, aggro in enumerate((1.0, 3.0, 9.0)):
        foe = Stats()
        foe.id = f"foe-{idx}"
        foe.hp = 1_000
        foe._base_defense = 0
        foe.base_aggro = aggro
        foe.apply_damage = types.MethodType(record_damage, foe)
        foes.append(foe)

    for _ in range(5):
        await actor.damage_type.ultimate(actor, [actor], foes)
        actor.ultimate_charge = actor.ultimate_charge_max
        actor.ultimate_ready = True

    assert sum(hits.values()) == 15
    assert hits.get("foe-2", 0) > hits.get("foe-1", 0) >= hits.get("foe-0", 0)
