import sys
from types import ModuleType

import pytest

from autofighter.effects import DamageOverTime
from autofighter.effects import EffectManager
from autofighter.effects import HealingOverTime
from autofighter.stats import Stats


@pytest.mark.asyncio
async def test_status_phase_events_emit_with_pacing(monkeypatch):
    target = Stats(hp=1000)
    target.set_base_stat('max_hp', 1000)
    target.set_base_stat('defense', 1)
    target.set_base_stat('mitigation', 1)
    target.set_base_stat('vitality', 1)
    target.id = "phase_target"

    manager = EffectManager(target)

    hot = HealingOverTime("regen", healing=10, turns=1, id="hot_1", source=target)
    dot = DamageOverTime("burn", damage=10, turns=1, id="dot_1", source=target)

    manager.add_hot(hot)
    manager.add_dot(dot)

    captured_events: list[tuple[str, tuple[object, ...]]] = []

    async def fake_emit_async(event: str, *args: object) -> None:
        captured_events.append((event, args))

    monkeypatch.setattr("autofighter.stats.BUS.emit_async", fake_emit_async)

    sleep_calls: list[float] = []
    expected_multiplier = 0.25

    async def fake_pace_sleep(multiplier: float = 1.0) -> None:
        sleep_calls.append(multiplier)

    pacing_stub = ModuleType("autofighter.rooms.battle.pacing")
    pacing_stub.YIELD_MULTIPLIER = expected_multiplier
    pacing_stub.pace_sleep = fake_pace_sleep

    monkeypatch.setitem(sys.modules, "autofighter.rooms.battle.pacing", pacing_stub)

    await manager.tick()

    assert sleep_calls == [expected_multiplier, expected_multiplier]

    status_events = [evt for evt in captured_events if evt[0].startswith("status_phase_")]
    assert [name for name, _ in status_events] == [
        "status_phase_start",
        "status_phase_end",
        "status_phase_start",
        "status_phase_end",
    ]

    start_hot_name, start_hot_args = status_events[0]
    assert start_hot_args[0] == "hot"
    assert start_hot_args[1] is target
    assert start_hot_args[2]["phase"] == "hot"
    assert start_hot_args[2]["effect_count"] == 1
    assert start_hot_args[2]["order"] == 0
    assert start_hot_args[2]["has_effects"] is True

    end_hot_name, end_hot_args = status_events[1]
    assert end_hot_args[2]["phase"] == "hot"
    assert end_hot_args[2]["effect_count"] == 0
    assert end_hot_args[2]["expired_count"] == 1
    assert end_hot_args[2]["order"] == 0

    start_dot_name, start_dot_args = status_events[2]
    assert start_dot_args[0] == "dot"
    assert start_dot_args[2]["phase"] == "dot"
    assert start_dot_args[2]["effect_count"] == 1
    assert start_dot_args[2]["order"] == 1

    end_dot_name, end_dot_args = status_events[3]
    assert end_dot_args[2]["phase"] == "dot"
    assert end_dot_args[2]["effect_count"] == 0
    assert end_dot_args[2]["expired_count"] == 1
    assert end_dot_args[2]["order"] == 1

    assert manager.hots == []
    assert manager.dots == []
