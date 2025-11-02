import asyncio
import random
import sys
import types

import pytest

from autofighter.party import Party
import autofighter.stats as stats
from plugins.characters._base import PlayerBase
from plugins.characters.foe_base import FoeBase
from plugins.effects.aftertaste import Aftertaste
import plugins.event_bus as event_bus_module
from plugins.relics.plague_harp import PlagueHarp


async def _drain_pending_tasks() -> None:
    await asyncio.sleep(0)
    await asyncio.sleep(0)
    await asyncio.sleep(0)


@pytest.fixture
def bus(monkeypatch):
    event_bus_module.bus._subs.clear()
    event_bus_module.bus._batched_events.clear()
    event_bus_module.bus._batch_timer = None

    bus = event_bus_module.EventBus()
    monkeypatch.setattr(stats, "BUS", bus)

    import plugins.relics.plague_harp as plague_module

    monkeypatch.setattr(plague_module, "BUS", bus)

    llms = types.ModuleType("llms")
    torch_checker = types.ModuleType("llms.torch_checker")
    torch_checker.is_torch_available = lambda: False
    llms.torch_checker = torch_checker
    monkeypatch.setitem(sys.modules, "llms", llms)
    monkeypatch.setitem(sys.modules, "llms.torch_checker", torch_checker)

    stats.set_battle_active(True)
    yield bus
    stats.set_battle_active(False)

    event_bus_module.bus._subs.clear()
    event_bus_module.bus._batched_events.clear()
    event_bus_module.bus._batch_timer = None


@pytest.mark.asyncio
async def test_plague_harp_echoes_to_other_foe(monkeypatch, bus):
    attacker = PlayerBase()
    attacker.hp = attacker.max_hp
    party = Party(members=[attacker], relics=["plague_harp"])
    relic = PlagueHarp()
    await relic.apply(party)

    calls: list[dict[str, object]] = []

    async def fake_aftertaste_apply(self, attacker_arg, target_arg):
        calls.append({
            "attacker": attacker_arg,
            "target": target_arg,
            "base_pot": self.base_pot,
        })
        return []

    monkeypatch.setattr(Aftertaste, "apply", fake_aftertaste_apply)
    monkeypatch.setattr(random.Random, "choice", lambda self, seq: seq[0])

    primary = FoeBase()
    secondary = FoeBase()

    await bus.emit_async("turn_start", primary)
    await bus.emit_async("turn_start", secondary)
    await _drain_pending_tasks()

    dot_amount = 250
    await bus.emit_async("dot_tick", attacker, primary, dot_amount, "burn", {"dot_id": "burn"})
    await _drain_pending_tasks()

    assert len(calls) == 1
    assert calls[0]["attacker"] is attacker
    assert calls[0]["target"] is secondary
    assert calls[0]["base_pot"] == max(1, int(dot_amount * 0.4))

    expected_tithe = max(1, int(attacker.max_hp * 0.02))
    assert attacker.hp == attacker.max_hp - expected_tithe


@pytest.mark.asyncio
async def test_plague_harp_falls_back_to_original_target(monkeypatch, bus):
    attacker = PlayerBase()
    attacker.hp = attacker.max_hp
    party = Party(members=[attacker], relics=["plague_harp", "plague_harp"])
    relic = PlagueHarp()
    await relic.apply(party)

    calls: list[dict[str, object]] = []

    async def fake_aftertaste_apply(self, attacker_arg, target_arg):
        calls.append({
            "attacker": attacker_arg,
            "target": target_arg,
            "base_pot": self.base_pot,
        })
        return []

    monkeypatch.setattr(Aftertaste, "apply", fake_aftertaste_apply)
    monkeypatch.setattr(random.Random, "choice", lambda self, seq: seq[0])

    primary = FoeBase()

    await bus.emit_async("turn_start", primary)
    await _drain_pending_tasks()

    dot_amount = 150
    await bus.emit_async("dot_tick", attacker, primary, dot_amount, "freeze", {"dot_id": "freeze"})
    await _drain_pending_tasks()

    assert len(calls) == 1
    assert calls[0]["target"] is primary
    assert calls[0]["base_pot"] == max(1, int(dot_amount * 0.4 * 2))

    expected_tithe = max(1, int(attacker.max_hp * 0.02 * 2))
    assert attacker.hp == attacker.max_hp - expected_tithe


@pytest.mark.asyncio
async def test_plague_harp_random_target_selection_respects_seed(monkeypatch, bus):
    attacker = PlayerBase()
    attacker.hp = attacker.max_hp
    party = Party(members=[attacker], relics=["plague_harp"])
    relic = PlagueHarp()
    await relic.apply(party)

    # Ensure a deterministic RNG so the target sequence is reproducible.
    state = getattr(party, "_plague_harp_state")
    rng_seed = 7
    state["rng"] = random.Random(rng_seed)

    calls: list[dict[str, object]] = []

    async def fake_aftertaste_apply(self, attacker_arg, target_arg):
        calls.append({
            "attacker": attacker_arg,
            "target": target_arg,
            "base_pot": self.base_pot,
        })
        return []

    monkeypatch.setattr(Aftertaste, "apply", fake_aftertaste_apply)

    primary = FoeBase()
    secondary = FoeBase()
    tertiary = FoeBase()

    await bus.emit_async("turn_start", primary)
    await bus.emit_async("turn_start", secondary)
    await bus.emit_async("turn_start", tertiary)
    await _drain_pending_tasks()

    reference_rng = random.Random(rng_seed)

    for _ in range(2):
        dot_amount = 200
        await bus.emit_async(
            "dot_tick",
            attacker,
            primary,
            dot_amount,
            "poison",
            {"dot_id": "poison"},
        )
        await _drain_pending_tasks()

    assert len(calls) == 2
    expected_first = reference_rng.choice([secondary, tertiary])
    expected_second = reference_rng.choice([secondary, tertiary])
    assert calls[0]["target"] is expected_first
    assert calls[1]["target"] is expected_second

@pytest.mark.asyncio
async def test_plague_harp_cleans_up_state_on_battle_end(bus):
    attacker = PlayerBase()
    attacker.hp = attacker.max_hp
    party = Party(members=[attacker], relics=["plague_harp"])
    relic = PlagueHarp()
    await relic.apply(party)

    assert hasattr(party, "_plague_harp_state")

    # Register a foe so the relic tracks them before cleanup.
    foe = FoeBase()
    await bus.emit_async("turn_start", foe)
    await _drain_pending_tasks()

    assert getattr(party, "_plague_harp_state")["foes"]

    await bus.emit_async("battle_end")
    await _drain_pending_tasks()

    assert not hasattr(party, "_plague_harp_state")
    subscriptions = getattr(party, "_relic_bus_subscriptions", {})
    assert "plague_harp" not in subscriptions
