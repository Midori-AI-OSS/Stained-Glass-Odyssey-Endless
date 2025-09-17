import pytest

from autofighter.passives import PassiveRegistry
import autofighter.stats as stats
from plugins.event_bus import EventBus


@pytest.fixture
def bus(monkeypatch):
    bus = EventBus()
    monkeypatch.setattr(stats, "BUS", bus)
    return bus


@pytest.fixture(autouse=True)
def battle_active():
    stats.set_battle_active(True)
    yield
    stats.set_battle_active(False)


@pytest.mark.asyncio
async def test_cost_damage_ignores_defense_and_shields(bus):
    s = stats.Stats()
    s._base_defense = 100000
    s.mitigation = 0.1
    s.shields = 200
    start_hp = s.hp
    await s.apply_cost_damage(150)
    assert s.hp == start_hp - 150
    assert s.shields == 200
    assert s.damage_taken == 150


@pytest.mark.asyncio
async def test_cost_damage_clamps_to_one_hp(bus):
    s = stats.Stats()
    s.hp = 50
    await s.apply_cost_damage(1000)
    assert s.hp == 1
    assert s.damage_taken == 1000


@pytest.mark.asyncio
async def test_normal_attack_respects_defense_and_shields(bus):
    s = stats.Stats()
    s._base_defense = 100000
    s.mitigation = 0.1
    s.shields = 200
    start_hp = s.hp
    attacker = stats.Stats()
    await s.apply_damage(150, attacker=attacker)
    assert s.hp == start_hp
    assert s.shields == 199
    assert s.damage_taken == 1


@pytest.mark.asyncio
async def test_cost_damage_triggers_damage_taken_passives(bus, monkeypatch):
    s = stats.Stats()
    called: dict[str, tuple] = {}

    async def fake_trigger(self, target, attacker, amount):
        called["args"] = (target, attacker, amount)

    monkeypatch.setattr(PassiveRegistry, "trigger_damage_taken", fake_trigger)
    await s.apply_cost_damage(42)
    assert called["args"] == (s, None, 42)
