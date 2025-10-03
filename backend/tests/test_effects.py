import asyncio
import importlib
import inspect
import sys
import types

import pytest

battle_logging = types.ModuleType("battle_logging")
battle_logging_writers = types.ModuleType("battle_logging.writers")
battle_logging_writers.end_battle_logging = lambda *_, **__: None
battle_logging_writers.BattleLogger = type("BattleLogger", (), {})
battle_logging_writers.start_battle_logging = lambda *_, **__: None
battle_logging.writers = battle_logging_writers
sys.modules.setdefault("battle_logging", battle_logging)
sys.modules.setdefault("battle_logging.writers", battle_logging_writers)

user_level_service = types.ModuleType("services.user_level_service")
user_level_service.gain_user_exp = lambda *_, **__: None
user_level_service.get_user_level = lambda *_, **__: 1
sys.modules.setdefault("services.user_level_service", user_level_service)

options_module = types.ModuleType("options")
options_module.OptionKey = type("OptionKey", (), {"TURN_PACING": "turn_pacing"})


def _options_get_option(*args, **kwargs):
    if len(args) >= 2:
        return args[1]
    if args:
        return args[0]
    return kwargs.get("default")


options_module.get_option = _options_get_option
sys.modules.setdefault("options", options_module)

llms_module = types.ModuleType("llms")
llms_loader = types.ModuleType("llms.loader")
llms_loader.ModelName = type("ModelName", (), {})
llms_loader.load_llm = lambda *_, **__: None
llms_module.loader = llms_loader
sys.modules.setdefault("llms", llms_module)
sys.modules.setdefault("llms.loader", llms_loader)

tts_module = types.ModuleType("tts")
tts_module.generate_voice = lambda *_, **__: None
sys.modules.setdefault("tts", tts_module)

effects = importlib.import_module("autofighter.effects")
EffectManager = getattr(effects, "EffectManager")
PassiveRegistry = getattr(importlib.import_module("autofighter.passives"), "PassiveRegistry")
turns = importlib.import_module("autofighter.rooms.battle.turns")
EnrageState = getattr(turns, "EnrageState")
apply_enrage_bleed = getattr(turns, "apply_enrage_bleed")
stats_module = importlib.import_module("autofighter.stats")
Stats = getattr(stats_module, "Stats")
set_battle_active = getattr(stats_module, "set_battle_active")
Fire = getattr(importlib.import_module("plugins.damage_types.fire"), "Fire")
EventBus = getattr(importlib.import_module("plugins.event_bus"), "EventBus")


def test_dot_applies_with_hit_rate():
    attacker = Stats(damage_type=Fire())
    attacker.set_base_stat('atk', 50)
    attacker.set_base_stat('effect_hit_rate', 2.0)
    target = Stats()
    target.set_base_stat('effect_resistance', 0.0)
    manager = EffectManager(target)
    manager.maybe_inflict_dot(attacker, 50)
    assert target.dots


def test_blazing_torment_stacks():
    attacker = Stats(damage_type=Fire())
    attacker.set_base_stat('atk', 50)
    attacker.set_base_stat('effect_hit_rate', 2.0)
    target = Stats()
    target.set_base_stat('effect_resistance', 0.0)
    manager = EffectManager(target)
    manager.maybe_inflict_dot(attacker, 50)
    manager.maybe_inflict_dot(attacker, 50)
    assert target.dots.count("blazing_torment") >= 2


def test_high_hit_rate_applies_multiple_stacks(monkeypatch):
    attacker = Stats(damage_type=Fire())
    attacker.set_base_stat('atk', 50)
    attacker.set_base_stat('effect_hit_rate', 3.5)
    target = Stats()
    target.set_base_stat('effect_resistance', 0.1)
    manager = EffectManager(target)
    monkeypatch.setattr(effects.random, "random", lambda: 0.0)
    manager.maybe_inflict_dot(attacker, 50)
    assert target.dots.count("blazing_torment") >= 3


@pytest.mark.asyncio
async def test_damage_and_heal_events():
    bus = EventBus()
    original_bus = getattr(stats_module, "BUS", None)
    stats_module.BUS = bus
    events = []

    def _dmg(target, attacker, amount, *_: object):
        events.append(("dmg", amount))

    def _heal(target, healer, amount, *_args):
        events.append(("heal", amount))

    bus.subscribe("damage_taken", _dmg)
    bus.subscribe("heal_received", _heal)
    attacker = Stats(damage_type=Fire())
    attacker.set_base_stat('atk', 10)
    target = Stats(hp=50)
    target.set_base_stat('max_hp', 100)
    set_battle_active(True)
    try:
        await target.apply_damage(10, attacker=attacker)
        await target.apply_healing(5, healer=attacker)
        await asyncio.sleep(0.05)
    finally:
        set_battle_active(False)
        bus.unsubscribe("damage_taken", _dmg)
        bus.unsubscribe("heal_received", _heal)
        stats_module.BUS = original_bus
    assert ("dmg", 1) in events and ("heal", 5) in events


@pytest.mark.asyncio
async def test_hot_ticks_before_dot():
    bus = EventBus()
    original_bus = getattr(stats_module, "BUS", None)
    stats_module.BUS = bus
    events = []

    def _dmg(target, attacker, amount, *_: object):
        events.append(("dmg", amount))

    def _heal(target, healer, amount, *_args):
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
    set_battle_active(True)
    try:
        await manager.tick()
        await asyncio.sleep(0.05)
    finally:
        set_battle_active(False)
        bus.unsubscribe("damage_taken", _dmg)
        bus.unsubscribe("heal_received", _heal)
        stats_module.BUS = original_bus
    assert events == [("heal", 10), ("dmg", 1)]
    assert target.hp == 99


@pytest.mark.asyncio
async def test_hot_minimum_tick_healing():
    bus = EventBus()
    original_bus = getattr(stats_module, "BUS", None)
    stats_module.BUS = bus
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
        await asyncio.sleep(0.05)
    finally:
        set_battle_active(False)
        bus.unsubscribe("hot_tick", _hot_tick)
        stats_module.BUS = original_bus

    assert heal_amounts == [1]
    assert target.hp == 6


@pytest.mark.asyncio
async def test_hot_effects_removed_when_target_is_dead():
    target = Stats()
    target.set_base_stat('max_hp', 10)
    target.set_base_stat('defense', 0)
    target.hp = 10
    manager = EffectManager(target)
    healer = Stats()

    hot = effects.HealingOverTime("regen", healing=5, turns=3, id="dead_hot", source=healer)
    manager.add_hot(hot)
    assert manager.hots

    set_battle_active(True)
    try:
        await target.apply_damage(10)
        assert target.hp == 0
        await manager.tick()
    finally:
        set_battle_active(False)

    assert target.hp == 0
    assert not manager.hots
    assert not target.hots


@pytest.mark.asyncio
async def test_zero_damage_dot_deals_minimum_one_per_stack():
    bus = EventBus()
    original_bus = getattr(stats_module, "BUS", None)
    stats_module.BUS = bus
    tick_amounts: list[int] = []

    def _dot_tick(_attacker, _target, amount, *_):
        tick_amounts.append(amount)

    bus.subscribe("dot_tick", _dot_tick)

    attacker = Stats()
    target = Stats()
    attacker.id = "attacker"
    target.id = "target"
    target.set_base_stat('max_hp', 10)
    target.hp = 10
    manager = EffectManager(target)

    manager.add_dot(effects.DamageOverTime("zero_dot", 0, 1, "zero_dot", source=attacker))
    manager.add_dot(effects.DamageOverTime("zero_dot", 0, 1, "zero_dot", source=attacker))

    set_battle_active(True)
    try:
        await manager.tick()
        await asyncio.sleep(0.05)
    finally:
        set_battle_active(False)
        bus.unsubscribe("dot_tick", _dot_tick)
        stats_module.BUS = original_bus

    assert tick_amounts == [1, 1]
    assert target.hp == 8


def test_dot_has_minimum_chance(monkeypatch):
    attacker = Stats(damage_type=Fire())
    attacker.set_base_stat('effect_hit_rate', 0.0)
    target = Stats()
    target.set_base_stat('effect_resistance', 5.0)
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


@pytest.mark.asyncio
async def test_damage_over_time_tick_awaits_pacing(monkeypatch):
    pacing = importlib.import_module("autofighter.rooms.battle.pacing")
    calls: list[tuple[str, float]] = []

    async def fake_sleep(multiplier: float = 1.0) -> None:
        frame = inspect.currentframe()
        caller = frame.f_back.f_locals.get("self") if frame and frame.f_back else None
        calls.append((type(caller).__name__ if caller is not None else "", multiplier))

    monkeypatch.setattr(pacing, "pace_sleep", fake_sleep)
    monkeypatch.setattr(pacing, "YIELD_MULTIPLIER", 0.25)

    target = Stats()
    target.set_base_stat('max_hp', 200)
    target.set_base_stat('defense', 0)
    target.hp = target.max_hp

    dot = effects.DamageOverTime("burn", damage=5, turns=1, id="burn")

    set_battle_active(True)
    try:
        await dot.tick(target)
    finally:
        set_battle_active(False)

    assert calls == [("DamageOverTime", pacing.YIELD_MULTIPLIER)]


@pytest.mark.asyncio
async def test_healing_over_time_tick_awaits_pacing(monkeypatch):
    pacing = importlib.import_module("autofighter.rooms.battle.pacing")
    calls: list[tuple[str, float]] = []

    async def fake_sleep(multiplier: float = 1.0) -> None:
        frame = inspect.currentframe()
        caller = frame.f_back.f_locals.get("self") if frame and frame.f_back else None
        calls.append((type(caller).__name__ if caller is not None else "", multiplier))

    monkeypatch.setattr(pacing, "pace_sleep", fake_sleep)
    monkeypatch.setattr(pacing, "YIELD_MULTIPLIER", 0.5)

    target = Stats()
    target.set_base_stat('max_hp', 100)
    target.hp = 50

    hot = effects.HealingOverTime("regen", healing=5, turns=1, id="regen")

    await hot.tick(target)

    assert calls == [("HealingOverTime", pacing.YIELD_MULTIPLIER)]
    assert target.hp > 50


@pytest.mark.asyncio
async def test_parallel_dot_ticks_respect_pacing(monkeypatch):
    pacing = importlib.import_module("autofighter.rooms.battle.pacing")
    calls: list[tuple[str, float]] = []

    async def fake_sleep(multiplier: float = 1.0) -> None:
        frame = inspect.currentframe()
        caller = frame.f_back.f_locals.get("self") if frame and frame.f_back else None
        calls.append((type(caller).__name__ if caller is not None else "", multiplier))

    monkeypatch.setattr(pacing, "pace_sleep", fake_sleep)
    monkeypatch.setattr(pacing, "YIELD_MULTIPLIER", 0.1)

    target = Stats()
    target.set_base_stat('max_hp', 500)
    target.set_base_stat('defense', 0)
    target.hp = target.max_hp

    manager = EffectManager(target)
    for idx in range(25):
        manager.add_dot(effects.DamageOverTime(f"burn{idx}", damage=1, turns=1, id=f"burn{idx}"))

    set_battle_active(True)
    try:
        await manager.tick()
    finally:
        set_battle_active(False)

    dot_calls = [call for call in calls if call[0] == "DamageOverTime"]
    manager_calls = [call for call in calls if call[0] == "EffectManager"]

    assert len(dot_calls) == 25
    assert all(multiplier == pacing.YIELD_MULTIPLIER for _, multiplier in dot_calls)
    assert len(manager_calls) >= 3


@pytest.mark.asyncio
async def test_self_inflicted_dot_uses_none_attacker(monkeypatch):
    target = Stats()
    target.set_base_stat('max_hp', 100)
    target.set_base_stat('defense', 0)
    target.hp = target.max_hp
    target.id = "self_dot"
    manager = EffectManager(target)
    target.effect_manager = manager

    recorded: list[object | None] = []
    original_trigger = PassiveRegistry.trigger_damage_taken

    async def _record(self, target_arg, attacker=None, damage=0):
        if target_arg is target:
            recorded.append(attacker)
        await original_trigger(self, target_arg, attacker, damage)

    monkeypatch.setattr(PassiveRegistry, "trigger_damage_taken", _record)

    manager.add_dot(effects.DamageOverTime("Self Burn", 10, 1, "self_burn", source=target))

    set_battle_active(True)
    try:
        await manager.tick()
    finally:
        set_battle_active(False)

    assert recorded == [None]
    assert target.damage_dealt == 0


@pytest.mark.asyncio
async def test_enrage_bleed_does_not_trigger_graygray_counter(monkeypatch):
    state = EnrageState(threshold=0, active=True, stacks=10, bleed_applies=0)
    graygray = Stats()
    graygray.set_base_stat('max_hp', 200)
    graygray.set_base_stat('defense', 0)
    graygray.hp = graygray.max_hp
    graygray.id = "graygray"
    graygray.passives.append("graygray_counter_maestro")
    graygray_manager = EffectManager(graygray)
    graygray.effect_manager = graygray_manager

    foe = Stats()
    foe.id = "foe"
    foe_manager = EffectManager(foe)
    foe.effect_manager = foe_manager

    recorded: list[object | None] = []
    original_trigger = PassiveRegistry.trigger_damage_taken

    async def _record(self, target_arg, attacker=None, damage=0):
        if target_arg is graygray:
            recorded.append(attacker)
        await original_trigger(self, target_arg, attacker, damage)

    monkeypatch.setattr(PassiveRegistry, "trigger_damage_taken", _record)

    set_battle_active(True)
    try:
        await apply_enrage_bleed(state, [graygray], [foe], [foe_manager])
        await graygray_manager.tick()
    finally:
        set_battle_active(False)

    assert state.bleed_applies == 1
    assert recorded == [None]
    assert graygray.damage_dealt == 0

