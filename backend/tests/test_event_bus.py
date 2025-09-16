import asyncio
import importlib.util
import logging
from pathlib import Path

from autofighter.rooms.battle.pacing import YIELD_DELAY

spec = importlib.util.spec_from_file_location(
    "event_bus", Path(__file__).resolve().parents[1] / "plugins" / "event_bus.py"
)
event_bus_module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(event_bus_module)
EventBus = event_bus_module.EventBus


def test_event_bus_emit_and_unsubscribe():
    bus = EventBus()
    received = []

    def handler(value):
        received.append(value)

    bus.subscribe("test", handler)
    bus.emit("test", 1)
    assert received == [1]
    bus.unsubscribe("test", handler)
    bus.emit("test", 2)
    assert received == [1]


def test_emit_batched_within_subscriber():
    bus = EventBus()
    received = []

    def inner_handler(value):
        received.append(value)

    def outer_handler(value):
        bus.emit_batched("inner", value + 1)

    bus.subscribe("inner", inner_handler)
    bus.subscribe("outer", outer_handler)

    bus.emit_batched("outer", 1)
    assert received == [2]

    bus.unsubscribe("inner", inner_handler)
    bus.unsubscribe("outer", outer_handler)


def test_dynamic_batch_interval_thresholds():
    async def run_scenario(existing: int) -> float:
        bus = EventBus()
        internal = event_bus_module.bus
        intervals = []

        async def capture(interval: float) -> None:
            intervals.append(interval)

        internal._process_batches_with_interval = capture  # type: ignore[assignment]
        internal._batched_events["test"] = [()] * existing
        bus.emit_batched("test", ())
        await asyncio.sleep(0)
        internal._batch_timer = None
        return intervals[0]

    interval_51 = asyncio.run(run_scenario(50))
    assert interval_51 == max(0.005, 0.016 * 0.5)

    interval_101 = asyncio.run(run_scenario(100))
    assert interval_101 == YIELD_DELAY


def test_emit_batched_without_loop_logs_debug(caplog):
    bus = EventBus()
    with caplog.at_level(logging.DEBUG, logger=event_bus_module.__name__):
        bus.emit_batched("test", ())

    messages = [record.getMessage() for record in caplog.records]
    assert any("No running event loop" in msg for msg in messages)
    assert all("RuntimeError" not in msg for msg in messages)


def test_async_callback_without_loop_avoids_runtime_error(caplog):
    bus = EventBus()

    async def handler(value):
        pass

    bus.subscribe("test", handler)

    with caplog.at_level(logging.WARNING, logger=event_bus_module.__name__):
        bus.emit("test", 1)

    messages = [record.getMessage() for record in caplog.records]
    assert any("called from sync context with no event loop" in msg for msg in messages)
    assert all("RuntimeError" not in msg for msg in messages)
