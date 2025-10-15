# Event Bus Wrapper

A lightweight publish/subscribe system so plugins can communicate without
engine‑specific dependencies. It supports both synchronous and asynchronous
callbacks and provides performance instrumentation.

## Usage
- `subscribe(event: str, callback: Callable)` – register a callback for an
  event. Callback may be sync or async.
- `unsubscribe(event: str, callback: Callable)` – remove a previously
  registered callback.
- `emit(event: str, *args)` – broadcast an event. When an event loop is
  running and async dispatch is preferred, emissions are batched for better
  throughput; otherwise callbacks run synchronously.
- `emit_async(event: str, *args)` – await completion of all callbacks. This
  calls the internal `send_async` implementation which awaits coroutine
  callbacks directly and offloads sync ones to a thread pool.

Battle-scoped plugins like cards and relics should unsubscribe their handlers
(e.g., on `battle_end`) to avoid lingering listeners across encounters.

Subscriber errors are caught and logged so one misbehaving plugin does not crash
others.

## Asynchronous dispatch
`EventBus.subscribe` detects coroutine functions and registers an async‑aware
wrapper. When events are emitted:

- `send_async` awaits coroutine callbacks directly and uses
  `loop.run_in_executor` only for synchronous functions. This avoids the
  thread‑pool hop for async subscribers.
- The synchronous `send` path schedules coroutine subscribers with
  `create_task` if a loop is running. If no loop is present, the bus logs a
  warning and the coroutine is not executed.

When writing coroutine callbacks, avoid long blocking operations. Offload any
CPU‑bound or blocking work to your own executor to keep the event loop
responsive.

## Batching and adaptive intervals
High‑frequency events (e.g. `damage_dealt`, `damage_taken`, `hit_landed`,
`heal_received`) are batched. Events collected within a frame (default
`16 ms`) are processed together to reduce overhead. The batch interval is
adaptive—when load is low, batches are processed more quickly; during heavy
load, the interval grows to maintain responsiveness.

The cooperative yield strategy is adaptive rather than fixed-delay. Each
callback records its execution time and only yields when work has consumed a
meaningful slice of the frame budget:

- When a callback (or the accumulated time since the last yield) exceeds
  **4 ms**, the bus schedules `await asyncio.sleep(0)` to hand control back to
  the loop without adding artificial latency.
- When the callback or accumulated time exceeds **20 ms**, the bus performs a
  short blocking yield (`await asyncio.sleep(0.001)`) to prevent CPU pegging in
  pathological cases.

This keeps short bursts responsive—no unnecessary idle sleeps—while preserving
back-pressure when plugins perform expensive work. Batch flattening uses the
same adaptive thresholds. Large spikes still yield, but the loop is no longer
throttled by unconditional sleeps between every queued emission.

### Instrumentation and benchmarking

You can capture before/after latency by sampling `bus.get_metrics()` or by
timing individual dispatches:

```python
import asyncio
from plugins.event_bus import EventBus, bus as internal_bus

async def benchmark_emit(event_name: str, *args) -> dict[str, float]:
    internal_bus.clear_metrics()
    await EventBus().emit_async(event_name, *args)
    return internal_bus.get_metrics().get(event_name, {})

async def main():
    bus = EventBus()

    async def slow_handler(value: int) -> None:
        await asyncio.sleep(0.025)

    bus.subscribe("benchmark", slow_handler)
    metrics = await benchmark_emit("benchmark", 1)
    print(f"avg={metrics['avg_time']:.4f}s max={metrics['max_time']:.4f}s")

asyncio.run(main())
```

Running the snippet before and after a change highlights the difference in
callback timing and whether the hard 1 ms cooperative yield engaged. During
battle setup you can wrap `emit_batched` similarly to confirm the batch
processor avoids extra idle time while still enforcing the hard limit.

## Events
The core combat engine emits a few global events that plugins may subscribe to:

- `damage_dealt(attacker, target, amount)`
- `damage_taken(target, attacker, amount)`
- `heal(healer, target, amount)`
- `heal_received(target, healer, amount)`
- `before_attack(attacker, target, metadata, action_name)` – emitted immediately before damage is resolved when a combatant
  attacks a target through the standard battle flow. `metadata` includes the staged `attack_index`, `attack_total`, and unique
  `attack_sequence` values when available so listeners can correlate against the upcoming hit.
- `hit_landed(attacker, target, amount, source_type="attack", source_name=None)` – emitted when a successful hit occurs

Plugins can define additional event names as needed.
