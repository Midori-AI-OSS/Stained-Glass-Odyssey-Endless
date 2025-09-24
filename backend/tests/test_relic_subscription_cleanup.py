"""Tests ensuring relic event handlers do not duplicate on reapplication."""

from __future__ import annotations

import pytest

from autofighter.party import Party
from autofighter.relics import apply_relics
from autofighter.relics import award_relic
from autofighter.stats import BUS
from autofighter.stats import Stats
from plugins import event_bus as event_bus_module
from plugins.relics._base import RelicBase


def _collect_events(relic_id: str, effect_key: str, events: list[tuple]) -> list[tuple]:
    """Return all recorded relic effect events matching the requested keys."""

    return [event for event in events if event[0] == relic_id and event[2] == effect_key]


@pytest.mark.asyncio
async def test_bent_dagger_handlers_run_once_after_reapply() -> None:
    event_bus_module.bus._subs.clear()

    party = Party()
    member = Stats()
    enemy = Stats()
    member.set_base_stat("atk", 100)
    enemy.hp = enemy.set_base_stat("max_hp", 10)
    party.members.append(member)

    award_relic(party, "bent_dagger")
    await apply_relics(party)
    await apply_relics(party)

    assert len(event_bus_module.bus._subs.get("damage_taken", [])) == 1

    events: list[tuple] = []
    BUS.subscribe("relic_effect", lambda *args: events.append(args))

    enemy.hp = 0
    await BUS.emit_async("damage_taken", enemy, member, 10)

    atk_events = _collect_events("bent_dagger", "atk_boost_applied", events)
    assert len(atk_events) == len(party.members)

    event_bus_module.bus._subs.clear()


@pytest.mark.asyncio
async def test_pocket_manual_reapply_only_triggers_once_per_cycle() -> None:
    event_bus_module.bus._subs.clear()

    party = Party()
    attacker = Stats()
    target = Stats()
    party.members.append(attacker)
    award_relic(party, "pocket_manual")

    await apply_relics(party)
    await apply_relics(party)

    assert len(event_bus_module.bus._subs.get("hit_landed", [])) == 1

    events: list[tuple] = []
    BUS.subscribe("relic_effect", lambda *args: events.append(args))

    for _ in range(10):
        await BUS.emit_async("hit_landed", attacker, target, 100)

    triggers = _collect_events("pocket_manual", "trigger_aftertaste", events)
    assert len(triggers) == 1

    event_bus_module.bus._subs.clear()


@pytest.mark.asyncio
async def test_omega_core_single_battle_start_subscription() -> None:
    event_bus_module.bus._subs.clear()

    party = Party()
    member = Stats()
    member.set_base_stat("atk", 100)
    party.members.append(member)

    award_relic(party, "omega_core")
    await apply_relics(party)
    await apply_relics(party)

    assert len(event_bus_module.bus._subs.get("battle_start", [])) == 1
    assert len(event_bus_module.bus._subs.get("turn_start", [])) == 1
    battle_end_subs = event_bus_module.bus._subs.get("battle_end", [])
    assert len(battle_end_subs) == 2
    store = getattr(party, "_relic_bus_subscriptions", {})
    entries = store.get("omega_core", [])
    assert sum(1 for _, _, is_cleanup in entries if is_cleanup) == 1

    event_bus_module.bus._subs.clear()


class _DummyRelic(RelicBase):
    id = "dummy_relic"


def test_subscribe_deduplicates_identical_callback() -> None:
    event_bus_module.bus._subs.clear()

    party = Party()
    relic = _DummyRelic()

    def _handler(*_args: object, **_kwargs: object) -> None:
        pass

    relic.subscribe(party, "hit_landed", _handler)
    relic.subscribe(party, "hit_landed", _handler)

    assert len(event_bus_module.bus._subs.get("hit_landed", [])) == 1
    store = getattr(party, "_relic_bus_subscriptions", {})
    assert len(store.get(relic.id, [])) == 2  # event + cleanup

    event_bus_module.bus._subs.clear()


@pytest.mark.asyncio
async def test_handlers_cleanup_across_battle_cycles() -> None:
    event_bus_module.bus._subs.clear()

    party = Party()
    member = Stats()
    party.members.append(member)

    award_relic(party, "pocket_manual")

    for _ in range(5):
        await apply_relics(party)
        assert len(event_bus_module.bus._subs.get("hit_landed", [])) == 1
        await BUS.emit_async("battle_end", None)
        assert len(event_bus_module.bus._subs.get("hit_landed", [])) == 0

    event_bus_module.bus._subs.clear()
