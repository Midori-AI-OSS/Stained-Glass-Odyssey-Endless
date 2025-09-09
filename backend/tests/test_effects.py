import pytest

import autofighter.effects as effects
from autofighter.effects import EffectManager
from autofighter.stats import Stats
from plugins.damage_types.fire import Fire
from plugins.event_bus import EventBus


def test_dot_applies_with_hit_rate():
    attacker = Stats(atk=50, effect_hit_rate=2.0, damage_type=Fire())
    target = Stats(effect_resistance=0.0)
    manager = EffectManager(target)
    manager.maybe_inflict_dot(attacker, 50)
    assert target.dots


def test_blazing_torment_stacks():
    attacker = Stats(atk=50, effect_hit_rate=2.0, damage_type=Fire())
    target = Stats(effect_resistance=0.0)
    manager = EffectManager(target)
    manager.maybe_inflict_dot(attacker, 50)
    manager.maybe_inflict_dot(attacker, 50)
    assert target.dots.count("blazing_torment") == 2


def test_high_hit_rate_applies_multiple_stacks(monkeypatch):
    attacker = Stats(atk=50, effect_hit_rate=3.5, damage_type=Fire())
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
    attacker = Stats(atk=10, damage_type=Fire())
    target = Stats(hp=50, max_hp=100)
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
    target = Stats(hp=95, max_hp=100, defense=0)
    target.id = "t"
    manager = EffectManager(target)
    manager.add_hot(effects.HealingOverTime("regen", 10, 1, "h"))
    manager.add_dot(effects.DamageOverTime("burn", 1, 1, "d"))
    await manager.tick()
    bus.unsubscribe("damage_taken", _dmg)
    bus.unsubscribe("heal_received", _heal)
    assert events == [("heal", 10), ("dmg", 1)]
    assert target.hp == 99


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
    stats = Stats(atk=10, defense=20)
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
