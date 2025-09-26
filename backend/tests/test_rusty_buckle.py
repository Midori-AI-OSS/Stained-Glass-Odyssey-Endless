import asyncio
import sys
import types

import pytest

from autofighter.party import Party
import autofighter.stats as stats
from plugins.effects.aftertaste import Aftertaste
import plugins.event_bus as event_bus_module
from plugins.characters.foe_base import FoeBase
from plugins.characters._base import PlayerBase
import plugins.relics.rusty_buckle as rb
from plugins.relics.rusty_buckle import RustyBuckle


@pytest.fixture
def bus(monkeypatch):
    event_bus_module.bus._subs.clear()
    event_bus_module.bus._batched_events.clear()
    event_bus_module.bus._batch_timer = None

    bus = event_bus_module.EventBus()
    monkeypatch.setattr(stats, "BUS", bus)
    monkeypatch.setattr(rb, "BUS", bus)

    llms = types.ModuleType("llms")
    torch_checker = types.ModuleType("llms.torch_checker")
    torch_checker.is_torch_available = lambda: False
    llms.torch_checker = torch_checker
    monkeypatch.setitem(sys.modules, "llms", llms)
    monkeypatch.setitem(sys.modules, "llms.torch_checker", torch_checker)

    async def simple_damage(self, amount, attacker=None, **kwargs):
        self.hp = max(self.hp - int(amount), 0)
        await bus.emit_async("damage_taken", self, attacker, amount)
        return int(amount)

    async def simple_heal(self, amount, healer=None):
        self.hp = min(self.hp + int(amount), self.max_hp)
        await bus.emit_async("heal_received", self, healer, amount, None, None)
        return int(amount)

    monkeypatch.setattr(PlayerBase, "apply_damage", simple_damage)
    monkeypatch.setattr(PlayerBase, "apply_healing", simple_heal)

    stats.set_battle_active(True)
    yield bus
    stats.set_battle_active(False)
    event_bus_module.bus._subs.clear()
    event_bus_module.bus._batched_events.clear()
    event_bus_module.bus._batch_timer = None


async def _drain_pending_tasks() -> None:
    await asyncio.sleep(0)
    await asyncio.sleep(0)


@pytest.mark.asyncio
async def test_all_allies_bleed_each_turn(bus):
    first = PlayerBase()
    second = PlayerBase()
    second._base_max_hp = 800
    second.hp = 800
    party = Party(members=[first, second], relics=["rusty_buckle"])
    relic = RustyBuckle()
    await relic.apply(party)

    foe = FoeBase()
    await bus.emit_async("turn_start", foe)
    await _drain_pending_tasks()
    for member in party.members:
        await bus.emit_async("turn_start", member)
    await _drain_pending_tasks()

    assert party.members[0].hp == 950
    assert party.members[1].hp == 760

    for member in party.members:
        await bus.emit_async("turn_start", member)
    await _drain_pending_tasks()

    assert party.members[0].hp == 900
    assert party.members[1].hp == 720


@pytest.mark.asyncio
async def test_aftertaste_triggers_on_cumulative_loss(monkeypatch, bus):
    party = Party(members=[PlayerBase(), PlayerBase()], relics=["rusty_buckle"])
    relic = RustyBuckle()
    await relic.apply(party)

    foe = FoeBase()
    await bus.emit_async("turn_start", foe)
    for member in party.members:
        await bus.emit_async("turn_start", member)
    await _drain_pending_tasks()

    hits = 0

    async def fake_apply(self, attacker, target):
        nonlocal hits
        hits += 1
        return []

    monkeypatch.setattr(Aftertaste, "apply", fake_apply)

    await party.members[0].apply_damage(1000)
    await _drain_pending_tasks()
    assert hits == 0

    await party.members[1].apply_damage(1000)
    await _drain_pending_tasks()
    assert hits == 5


@pytest.mark.asyncio
async def test_stacks_increase_threshold(monkeypatch, bus):
    first = PlayerBase()
    second = PlayerBase()
    first._base_max_hp = 500
    first.hp = 500
    second._base_max_hp = 500
    second.hp = 500
    party = Party(members=[first, second], relics=["rusty_buckle", "rusty_buckle"])
    relic = RustyBuckle()
    await relic.apply(party)

    foe = FoeBase()
    await bus.emit_async("turn_start", foe)
    for member in party.members:
        await bus.emit_async("turn_start", member)
    await _drain_pending_tasks()

    hits = 0

    async def fake_apply(self, attacker, target):
        nonlocal hits
        hits += 1
        return []

    monkeypatch.setattr(Aftertaste, "apply", fake_apply)

    await party.members[0].apply_damage(500)
    await party.members[0].apply_healing(500)
    await party.members[0].apply_damage(500)
    await _drain_pending_tasks()
    assert hits == 0

    await party.members[1].apply_damage(500)
    await _drain_pending_tasks()
    assert hits == 8


@pytest.mark.asyncio
async def test_apply_no_type_error(bus):
    party = Party(members=[PlayerBase(), PlayerBase()], relics=["rusty_buckle"])
    relic = RustyBuckle()
    await relic.apply(party)
