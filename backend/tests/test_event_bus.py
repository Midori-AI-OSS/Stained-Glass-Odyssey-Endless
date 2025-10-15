import asyncio
import importlib.util
import logging
from collections.abc import Awaitable, Callable
from pathlib import Path
import sys
import types

import pytest

if "battle_logging" not in sys.modules:
    _battle_logging = types.ModuleType("battle_logging")
    _battle_logging.writers = types.ModuleType("battle_logging.writers")

    class _StubBattleLogger:
        def __init__(self, *args, **kwargs):
            return None

        async def log(self, *args, **kwargs) -> None:
            return None

    _battle_logging.writers.BattleLogger = _StubBattleLogger
    async def _noop_async(*args, **kwargs):
        return None

    _battle_logging.writers.BattleLogger = _StubBattleLogger
    _battle_logging.writers.end_battle_logging = lambda *args, **kwargs: None
    _battle_logging.writers.start_battle_logging = _noop_async
    _battle_logging.writers.end_run_logging = _noop_async
    sys.modules["battle_logging"] = _battle_logging
    sys.modules["battle_logging.writers"] = _battle_logging.writers

if "services.user_level_service" not in sys.modules:
    services_module = types.ModuleType("services")
    user_level_service = types.ModuleType("services.user_level_service")
    user_level_service.gain_user_exp = lambda *args, **kwargs: None
    user_level_service.get_user_level = lambda *args, **kwargs: 1
    services_module.user_level_service = user_level_service
    sys.modules["services"] = services_module
    sys.modules["services.user_level_service"] = user_level_service

    if "services.room_service" not in sys.modules:
        room_service = types.ModuleType("services.room_service")
        room_service.get_room = lambda *args, **kwargs: None
        services_module.room_service = room_service
        sys.modules["services.room_service"] = room_service

if "options" not in sys.modules:
    _options = types.ModuleType("options")
    class OptionKey:
        pass

    def get_option(key, default=None):
        return default

    _options.OptionKey = OptionKey
    _options.get_option = get_option
    sys.modules["options"] = _options

if "llms.loader" not in sys.modules:
    llms_module = types.ModuleType("llms")
    loader_module = types.ModuleType("llms.loader")
    loader_module.ModelName = type("ModelName", (), {})
    loader_module.load_llm = lambda *args, **kwargs: None
    loader_module._IMPORT_ERROR = None
    torch_checker_module = types.ModuleType("llms.torch_checker")
    torch_checker_module.is_torch_available = lambda: False
    llms_module.loader = loader_module
    llms_module.torch_checker = torch_checker_module
    sys.modules["llms"] = llms_module
    sys.modules["llms.loader"] = loader_module
    sys.modules["llms.torch_checker"] = torch_checker_module

if "tts" not in sys.modules:
    tts_module = types.ModuleType("tts")
    async def _generate_voice(*args, **kwargs):
        return None

    tts_module.generate_voice = _generate_voice
    sys.modules["tts"] = tts_module

from autofighter.rooms.battle.pacing import YIELD_DELAY

spec = importlib.util.spec_from_file_location(
    "event_bus", Path(__file__).resolve().parents[1] / "plugins" / "event_bus.py"
)
event_bus_module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(event_bus_module)
EventBus = event_bus_module.EventBus


@pytest.mark.asyncio
async def test_event_bus_emit_async_and_unsubscribe():
    bus = EventBus()
    received: list[tuple[str, int]] = []

    async def async_handler(value: int) -> None:
        received.append(("async", value))

    def sync_handler(value: int) -> None:
        received.append(("sync", value))

    bus.subscribe("test", async_handler)
    bus.subscribe("test", sync_handler)

    await bus.emit_async("test", 1)

    assert {tuple(event) for event in received} == {("async", 1), ("sync", 1)}

    bus.unsubscribe("test", async_handler)
    bus.unsubscribe("test", sync_handler)
    received.clear()

    await bus.emit_async("test", 2)

    assert received == []


@pytest.mark.asyncio
async def test_emit_batched_within_subscriber():
    bus = EventBus()
    received: list[int] = []
    inner_seen = asyncio.Event()

    async def inner_handler(value: int) -> None:
        received.append(value)
        inner_seen.set()

    def outer_handler(value: int) -> None:
        bus.emit_batched("inner", value + 1)

    bus.subscribe("inner", inner_handler)
    bus.subscribe("outer", outer_handler)

    await bus.emit_async("outer", 1)
    await asyncio.wait_for(inner_seen.wait(), timeout=1)

    assert received == [2]

    bus.unsubscribe("inner", inner_handler)
    bus.unsubscribe("outer", outer_handler)


@pytest.mark.asyncio
async def test_dynamic_batch_interval_thresholds():
    async def run_scenario(existing: int) -> float:
        bus = EventBus()
        internal = event_bus_module.bus
        intervals: list[float] = []
        triggered = asyncio.Event()

        async def capture(interval: float) -> None:
            intervals.append(interval)
            triggered.set()

        original = internal._process_batches_with_interval
        try:
            internal._process_batches_with_interval = capture  # type: ignore[assignment]
            internal._batched_events["test"] = [()] * existing
            bus.emit_batched("test", ())
            await asyncio.wait_for(triggered.wait(), timeout=1)
            internal._batch_timer = None
        finally:
            internal._process_batches_with_interval = original
            internal._batched_events.clear()

        return intervals[0]

    interval_51 = await run_scenario(50)
    assert interval_51 == max(0.005, 0.016 * 0.5)

    interval_101 = await run_scenario(100)
    assert interval_101 == YIELD_DELAY


@pytest.mark.asyncio
async def test_emit_batched_async_flushes_with_stored_loop(caplog):
    bus = EventBus()
    loop = asyncio.get_running_loop()
    bus.set_loop(loop)

    seen = asyncio.Event()

    async def handler(value: int) -> None:
        seen.set()

    bus.subscribe("test", handler)

    with caplog.at_level(logging.WARNING, logger=event_bus_module.__name__):
        await bus.emit_batched_async("test", 1)
        await asyncio.wait_for(seen.wait(), timeout=1)

    assert [
        record for record in caplog.records if record.levelno >= logging.WARNING
    ] == []

    bus.unsubscribe("test", handler)


@pytest.mark.asyncio
async def test_emit_async_triggers_nested_batched_event_on_loop():
    bus = EventBus()
    internal = event_bus_module.bus
    internal._process_batches_with_interval = event_bus_module._Bus._process_batches_with_interval.__get__(
        internal, event_bus_module._Bus
    )
    internal._process_batches = event_bus_module._Bus._process_batches.__get__(
        internal, event_bus_module._Bus
    )
    internal._process_batches_internal = event_bus_module._Bus._process_batches_internal.__get__(
        internal, event_bus_module._Bus
    )
    internal._batched_events.clear()
    internal._batch_timer = None

    outer_complete = asyncio.Event()
    inner_seen = asyncio.Event()

    async def inner_handler(value: int) -> None:
        inner_seen.set()

    def outer_handler(value: int) -> None:
        bus.emit_batched("inner", value + 1)
        outer_complete.set()

    bus.subscribe("inner", inner_handler)
    bus.subscribe("outer", outer_handler)

    await bus.emit_async("outer", 1)

    await asyncio.wait_for(outer_complete.wait(), timeout=1)
    await asyncio.wait_for(inner_seen.wait(), timeout=1)

    bus.unsubscribe("inner", inner_handler)
    bus.unsubscribe("outer", outer_handler)


@pytest.mark.asyncio
async def test_emit_async_skips_hard_sleep_for_quick_callbacks(monkeypatch):
    bus = EventBus()
    recorded: list[float] = []
    original_sleep = event_bus_module.asyncio.sleep

    async def tracking_sleep(delay: float, *args, **kwargs):
        recorded.append(delay)
        return await original_sleep(delay)

    monkeypatch.setattr(event_bus_module.asyncio, "sleep", tracking_sleep)

    handlers: list[Callable[[int], Awaitable[None]]] = []

    for idx in range(8):
        async def handler(value: int, idx: int = idx) -> None:
            _ = value + idx

        handlers.append(handler)
        bus.subscribe("adaptive", handler)

    await bus.emit_async("adaptive", 5)

    for handler in handlers:
        bus.unsubscribe("adaptive", handler)

    assert not any(
        abs(delay - event_bus_module._HARD_YIELD_DELAY) < 1e-6
        for delay in recorded
        if delay > 0
    )


@pytest.mark.asyncio
async def test_emit_async_hard_sleep_for_slow_callback(monkeypatch):
    bus = EventBus()
    recorded: list[float] = []
    original_sleep = event_bus_module.asyncio.sleep

    async def tracking_sleep(delay: float, *args, **kwargs):
        recorded.append(delay)
        return await original_sleep(delay)

    monkeypatch.setattr(event_bus_module.asyncio, "sleep", tracking_sleep)

    async def slow_handler(value: int) -> None:
        await original_sleep(event_bus_module._HARD_YIELD_THRESHOLD + 0.005)

    bus.subscribe("adaptive", slow_handler)

    await bus.emit_async("adaptive", 5)

    bus.unsubscribe("adaptive", slow_handler)

    assert any(
        abs(delay - event_bus_module._HARD_YIELD_DELAY) < 2e-4
        for delay in recorded
        if delay > 0
    )


@pytest.mark.asyncio
async def test_batched_processing_uses_adaptive_yield(monkeypatch):
    bus = EventBus()
    recorded: list[float] = []
    original_sleep = event_bus_module.asyncio.sleep

    async def tracking_sleep(delay: float, *args, **kwargs):
        recorded.append(delay)
        return await original_sleep(delay)

    monkeypatch.setattr(event_bus_module.asyncio, "sleep", tracking_sleep)

    processed = asyncio.Event()
    total = 6
    counter = 0

    async def slow_handler(value: int) -> None:
        nonlocal counter
        await original_sleep(event_bus_module._HARD_YIELD_THRESHOLD + 0.004)
        counter += 1
        if counter == total:
            processed.set()

    bus.subscribe("batch", slow_handler)

    for idx in range(total):
        bus.emit_batched("batch", idx)

    await asyncio.wait_for(processed.wait(), timeout=2)

    bus.unsubscribe("batch", slow_handler)

    assert any(
        abs(delay - event_bus_module._HARD_YIELD_DELAY) < 5e-4
        for delay in recorded
        if abs(delay - event_bus_module.bus._batch_interval) > 1e-6 and delay > 0
    )
