# Battle Setup Thread Offloading

The battle setup routine performs a few heavy operations that would otherwise block the event loop:

- Deep cloning each `Stats` instance in the party before combat begins.
- Applying relic effects, which mutates the party and can perform database or file lookups depending on relic behavior.

To keep setup responsive, both steps are dispatched to worker threads via `asyncio.to_thread()`:

- `_clone_members()` wraps the `copy.deepcopy` call so member cloning runs in a thread pool and returns the cloned list asynchronously.
- `_apply_relics_async()` forwards the existing `apply_relics()` call to a worker thread and awaits completion.

`setup_battle()` awaits both helpers, ensuring callers see consistent state without blocking other async tasks while the work is performed.
