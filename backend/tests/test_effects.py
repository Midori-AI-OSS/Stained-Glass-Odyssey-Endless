import pytest

import autofighter.effects as effects
from autofighter.effects import EffectManager
from autofighter.stats import Stats
from autofighter.stats import set_battle_active
from plugins.damage_types.fire import Fire
from plugins.event_bus import EventBus


def test_dot_applies_with_hit_rate():
    attacker = Stats(damage_type=Fire())
    attacker.set_base_stat('atk', 50)
    attacker.set_base_stat('effect_hit_rate', 2.0)
    target = Stats(effect_resistance=0.0)
    manager = EffectManager(target)
    manager.maybe_inflict_dot(attacker, 50)
    assert target.dots


def test_blazing_torment_stacks():
    attacker = Stats(damage_type=Fire())
    attacker.set_base_stat('atk', 50)
    attacker.set_base_stat('effect_hit_rate', 2.0)
    target = Stats(effect_resistance=0.0)
    manager = EffectManager(target)
    manager.maybe_inflict_dot(attacker, 50)
    manager.maybe_inflict_dot(attacker, 50)
    assert target.dots.count("blazing_torment") == 2


def test_high_hit_rate_applies_multiple_stacks(monkeypatch):
    attacker = Stats(damage_type=Fire())
    attacker.set_base_stat('atk', 50)
    attacker.set_base_stat('effect_hit_rate', 3.5)
    target = Stats(effect_resistance=0.1)
    manager = EffectManager(target)
    monkeypatch.setattr(effects.random, "random", lambda: 0.0)
    manager.maybe_inflict_dot(attacker, 50)
    assert target.dots.count("blazing_torment") >= 3


@pytest.mark.asyncio
async def test_damage_and_heal_events():
    bus = EventBus()
    events = []

    def _dmg(target, attacker, amount):
        events.append(("dmg", amount))

    def _heal(target, healer, amount):
        events.append(("heal", amount))

    bus.subscribe("damage_taken", _dmg)
    bus.subscribe("heal_received", _heal)
    attacker = Stats(damage_type=Fire())
    attacker.set_base_stat('atk', 10)
    target = Stats(hp=50)
    target.set_base_stat('max_hp', 100)
    await target.apply_damage(10, attacker=attacker)
    await target.apply_healing(5, healer=attacker)
    bus.unsubscribe("damage_taken", _dmg)
    bus.unsubscribe("heal_received", _heal)
    assert ("dmg", 1) in events and ("heal", 5) in events


@pytest.mark.asyncio
async def test_hot_ticks_before_dot():
    bus = EventBus()
    events = []

    def _dmg(target, attacker, amount):
        events.append(("dmg", amount))

    def _heal(target, healer, amount):
        events.append(("heal", amount))

    bus.subscribe("damage_taken", _dmg)
    bus.subscribe("heal_received", _heal)
    target = Stats(hp=95)
    target.set_base_stat('max_hp', 100)
    target.set_base_stat('defense', 0)
    target.id = "t"
    manager = EffectManager(target)
    manager.add_hot(effects.HealingOverTime("regen", 10, 1, "h"))
    manager.add_dot(effects.DamageOverTime("burn", 1, 1, "d"))
    await manager.tick()
    bus.unsubscribe("damage_taken", _dmg)
    bus.unsubscribe("heal_received", _heal)
    assert events == [("heal", 10), ("dmg", 1)]
    assert target.hp == 99


@pytest.mark.asyncio
async def test_hot_minimum_tick_healing():
    bus = EventBus()
    heal_amounts = []

    def _hot_tick(_healer, _target, amount, *_):
        heal_amounts.append(amount)

    bus.subscribe("hot_tick", _hot_tick)

    target = Stats()
    target.set_base_stat('max_hp', 10)
    target.hp = 5
    manager = EffectManager(target)
    healer = Stats()

    manager.add_hot(effects.HealingOverTime("regen", 0, 1, "hot_min", source=healer))

    set_battle_active(True)
    try:
        await manager.tick()
    finally:
        set_battle_active(False)
        bus.unsubscribe("hot_tick", _hot_tick)

    assert heal_amounts == [1]
    assert target.hp == 6


@pytest.mark.asyncio
async def test_zero_damage_dot_deals_minimum_one_per_stack():
    bus = EventBus()
    tick_amounts: list[int] = []

    def _dot_tick(_attacker, _target, amount, *_):
        tick_amounts.append(amount)

    bus.subscribe("dot_tick", _dot_tick)

    attacker = Stats()
    target = Stats()
    target.set_base_stat('max_hp', 10)
    target.hp = 10
    manager = EffectManager(target)

    manager.add_dot(effects.DamageOverTime("zero_dot", 0, 1, "zero_dot", source=attacker))
    manager.add_dot(effects.DamageOverTime("zero_dot", 0, 1, "zero_dot", source=attacker))

    set_battle_active(True)
    try:
        await manager.tick()
    finally:
        set_battle_active(False)
        bus.unsubscribe("dot_tick", _dot_tick)

    assert tick_amounts == [1, 1]
    assert target.hp == 8


def test_dot_has_minimum_chance(monkeypatch):
    attacker = Stats(effect_hit_rate=0.0, damage_type=Fire())
    target = Stats(effect_resistance=5.0)
    manager = EffectManager(target)
    monkeypatch.setattr(effects.random, "uniform", lambda a, b: 1.0)
    monkeypatch.setattr(effects.random, "random", lambda: 0.0)
    manager.maybe_inflict_dot(attacker, 10)
    assert target.dots


@pytest.mark.asyncio
async def test_stat_modifier_applies_and_expires():
    stats = Stats()
    stats.set_base_stat('atk', 10)
    stats.set_base_stat('defense', 20)
    stats.id = "s"
    manager = EffectManager(stats)
    mod = effects.create_stat_buff(
        stats,
        name="rally",
        turns=1,
        atk=5,
        defense_mult=2,
    )
    manager.add_modifier(mod)
    assert stats.atk == 15
    assert stats.defense == 40
    await manager.tick()
    assert stats.atk == 10
    assert stats.defense == 20
    assert not stats.mods

