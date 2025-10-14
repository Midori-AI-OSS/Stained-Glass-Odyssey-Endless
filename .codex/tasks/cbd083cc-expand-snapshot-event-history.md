# Expand combat snapshot event history to prevent missing actions

## Summary
The snapshot overlay only keeps the six most recent events per run. When pacing lags, new events overwrite older ones before the frontend polls, so attacks and relic triggers vanish from the UI. We should retain a deeper history (or stream deltas) so the overlay reflects everything that happened.

## Details
* `_RECENT_EVENT_LIMIT` is hardcoded to 6 and the per-run deque is cleared on prepare, so a burst of more than six events drops earlier entries outright.【F:backend/autofighter/rooms/battle/snapshots.py†L12-L37】
* Battle setup and the first turn easily emit dozens of events (extra turns, buffs, heals), which means the frontend only ever sees the tail end of the burst when it finally renders.

## Requirements
- Decide on a richer retention strategy (larger deque size, per-event type buckets, or streamed pagination) that keeps enough context for normal combats.
- Update the overlay mutation logic and any consumers to handle the deeper history efficiently (avoid ballooning payloads for marathon runs).
- Add regression coverage ensuring at least N events survive a burst (e.g., simulate 20 quick emits and assert the client-visible list keeps them).
- Document the new retention policy for UI developers.
