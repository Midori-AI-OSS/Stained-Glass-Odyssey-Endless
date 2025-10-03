import asyncio

import pytest

from autofighter.effects import DamageOverTime
from autofighter.effects import EffectManager
from autofighter.stats import Stats
from autofighter.stats import set_battle_active
from plugins.damage_types.lightning import Lightning


@pytest.mark.asyncio
async def test_lightning_pop_damage_and_stacks():
    lightning = Lightning()
    attacker = Stats(damage_type=lightning)
    attacker.set_base_stat('atk', 0)
    attacker.id = "attacker"
    target = Stats(hp=100)
    target.set_base_stat('max_hp', 100)
    target.set_base_stat('defense', 1)
    target.set_base_stat('mitigation', 1.0)
    target.set_base_stat('vitality', 1.0)
    target.set_base_stat('dodge_odds', 0.0)
    target.id = "target"
    target.hp = target.max_hp
    target.effect_manager = EffectManager(target)

    dot1 = DamageOverTime("Test", 40, 3, "t1", attacker)
    dot2 = DamageOverTime("Test2", 20, 5, "t2", attacker)
    target.effect_manager.add_dot(dot1)
    target.effect_manager.add_dot(dot2)
    initial_turns = [d.turns for d in target.effect_manager.dots]
    initial_count = len(target.effect_manager.dots)
    start_hp = target.hp

    base = await target.apply_damage(0, attacker=attacker)
    await asyncio.sleep(0)
    dummy = Stats(hp=start_hp)
    dummy.set_base_stat('max_hp', start_hp)
    dummy.set_base_stat('defense', 1)
    dummy.set_base_stat('mitigation', 1.0)
    dummy.set_base_stat('vitality', 1.0)
    dummy.id = "dummy"
    dmg1 = await dummy.apply_damage(int(dot1.damage * 0.25), attacker=attacker)
    dummy.hp = start_hp
    dmg2 = await dummy.apply_damage(int(dot2.damage * 0.25), attacker=attacker)
    expected = max(start_hp - base - dmg1 - dmg2, 0)
    assert target.hp == expected
    assert [d.turns for d in target.effect_manager.dots] == initial_turns
    assert len(target.effect_manager.dots) == initial_count


@pytest.mark.asyncio
async def test_lightning_dot_ticks_do_not_trigger_on_hit():
    lightning = Lightning()
    attacker = Stats(damage_type=lightning)
    attacker.set_base_stat('atk', 0)
    attacker.id = "attacker"

    target = Stats(hp=100)
    target.set_base_stat('max_hp', 100)
    target.set_base_stat('defense', 1)
    target.set_base_stat('mitigation', 1.0)
    target.set_base_stat('vitality', 1.0)
    target.set_base_stat('dodge_odds', 0.0)
    target.id = "target"
    target.hp = target.max_hp
    target.effect_manager = EffectManager(target)

    dot = DamageOverTime("Lightning DoT", 20, 2, "lightning_dot", attacker)
    target.effect_manager.add_dot(dot)

    calls: list[bool] = []
    original_apply_damage = target.__class__.apply_damage

    async def recording_apply_damage(self, amount, *args, **kwargs):
        calls.append(kwargs.get("trigger_on_hit", True))
        return await original_apply_damage(self, amount, *args, **kwargs)

    target.apply_damage = recording_apply_damage.__get__(target, target.__class__)

    set_battle_active(True)
    try:
        await dot.tick(target)
        await asyncio.sleep(0)

        assert calls == [False]

        calls.clear()
        target.hp = target.max_hp

        await target.apply_damage(10, attacker=attacker)
        await asyncio.sleep(0)

        assert calls and calls[0] is True
        assert any(not value for value in calls[1:])
    finally:
        set_battle_active(False)
