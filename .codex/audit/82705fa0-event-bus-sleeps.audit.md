# Audit – Trim EventBus cooperative sleeps (Task 185897b3)

## Scope Reviewed
- backend/plugins/event_bus.py
- backend/tests/test_event_bus.py
- .codex/implementation/event-bus.md
- Task notes and historical review context in .codex/review/2025-02-15-task-audit.md
- Battle pacing defaults referenced by the EventBus fast-path (backend/autofighter/rooms/battle/pacing.py)

## Findings
### ✅ Requirements satisfied
1. **Adaptive cooperative yields** – The hard-coded 2 ms sleeps after every callback have been replaced by an adaptive helper that only yields once callback work crosses soft (4 ms) or hard (20 ms) thresholds, falling back to a 1 ms delay only when necessary. Batched dispatch now shares the same helper so short bursts no longer pay unconditional idle time.【F:backend/plugins/event_bus.py†L49-L124】【F:backend/plugins/event_bus.py†L250-L302】【F:backend/plugins/event_bus.py†L323-L370】
2. **Cooperative behavior preserved** – Async callback dispatch still runs concurrently, but updates a shared `_CooperativeState` protected by a lock so the loop yields when long-running handlers complete. Batched processing likewise fans out work in chunks of 100 with cooperative pauses between groups, preventing starvation without reintroducing the fixed sleeps.【F:backend/plugins/event_bus.py†L281-L302】【F:backend/plugins/event_bus.py†L323-L361】
3. **Dynamic batching** – The queue depth now tunes the batch interval (full frame, half frame, or the pacing module’s `YIELD_DELAY`), so high-traffic bursts flush almost immediately while light load keeps the previous cadence.【F:backend/plugins/event_bus.py†L203-L244】【F:backend/plugins/event_bus.py†L216-L233】【F:backend/autofighter/rooms/battle/pacing.py†L5-L38】
4. **Documentation and instrumentation** – The Event Bus implementation guide documents the new thresholds and includes a runnable snippet that records before/after timings via `bus.get_metrics()`, satisfying the instrumentation requirement.【F:.codex/implementation/event-bus.md†L40-L94】
5. **Regression coverage** – New pytest cases verify that quick callbacks avoid the hard 1 ms yield, slow callbacks trigger it, batched handlers honor the adaptive policy, and the dynamic interval thresholds resolve as expected.【F:backend/tests/test_event_bus.py†L108-L199】

### ⚠️ Observations
- The adaptive helper relies on hard-coded 4 ms/20 ms thresholds. They match the doc description, but consider promoting them to settings if further tuning is needed once broader combat benchmarks run. No action required before merge.

## Verification
- `uv venv && uv sync`
- `uv run pytest tests/test_event_bus.py`

## Recommendation
All acceptance criteria are met. I recommend Task Master approval.
