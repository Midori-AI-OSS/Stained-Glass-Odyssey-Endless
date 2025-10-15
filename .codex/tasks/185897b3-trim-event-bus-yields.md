# Trim EventBus cooperative sleeps to unblock combat pacing

## Summary
The EventBus injects 2 ms `asyncio.sleep` calls for every batched event and every subscriber callback, so large combat bursts accumulate tens of seconds of idle time before actions render. We need to keep cooperative scheduling without throttling the loop on hot paths.

## Details
* Batched dispatch spends 2 ms per queued event when flattening and again after each gathered batch, even before any subscriber work runs.【F:backend/plugins/event_bus.py†L202-L237】
* Each subscriber invocation in `send_async` sleeps for 2 ms after the callback, so decks/relics with dozens of listeners stall the loop by >100 ms per emission.【F:backend/plugins/event_bus.py†L267-L284】
* Setup sequences emit hundreds of events (card/relic applications, extra turns, rewards), so the forced sleeps expand the “battle start” delay into 45 s–3 min when the queue is busy.

## Requirements
- Replace the fixed 2 ms sleeps with an adaptive strategy (e.g., yielding only after X ms of actual work or when the loop is saturated) that keeps responsiveness but eliminates unnecessary idle time for bursts under typical load.
- Preserve cooperative behavior for pathological cases (no tight loops pegging the CPU) and document the new pacing policy.
- Provide benchmarks or instrumentation snippets demonstrating the before/after latency for a representative battle setup.
- Update or add tests covering batched dispatch and async subscribers so CI exercises the new pacing rules.

ready for review

requesting review from the Task Master
