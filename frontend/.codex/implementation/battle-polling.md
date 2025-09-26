# Battle polling

Battle cadence is now orchestrated by
`frontend/src/lib/systems/pollingOrchestrator.js`. The root controller exposes
three coordinated loops:

1. **UI state polling** — mirrors `/ui` responses, applies them to
   `runStateStore`, and notifies registered handlers. This loop pauses whenever
   `overlayBlocking`, `haltSync`, or a non-main overlay view is active.
2. **Battle snapshot polling** — automatically starts when
   `runStateStore.battleActive` flips to `true` and a run id is present. The
   controller fetches `room_action(snapshot)` payloads, normalizes fighter
   statuses, pushes results through `runStateStore`, and invokes configured
   callbacks so `+page.svelte` can surface overlays or auto-advance rooms.
3. **Map fallback polling** — resumes on non-battle ticks to keep map metadata
   current. If `/ui` bootstrap fails or rewards flows clear `roomData`, this
   loop falls back to `getMap` to rehydrate party, room, and snapshot state.

### Snapshot lifecycle

* On each tick the battle poller enforces the same three-second timeout window
  used previously. Consecutive `snapshot_missing` responses increment a counter;
  exceeding the threshold clears `battleActive`, emits an error overlay through
  the configured handler, and immediately schedules a map refresh.
* Snapshot payloads with an `error` field halt polling, persist the data via
  `runStateStore`, and allow the root page to surface error overlays.
* Rewards and completion flags (`awaiting_next`, `next_room`, or
  `result: 'defeat'`) stop the battle loop. The controller updates current/next
  room metadata in the store, invokes the completion callback (for defeat or
  reward overlays), and triggers the map poller so the UI can resume normal
  cadence.
* Stalled combat where both sides are defeated but no rewards arrive still
  yields a synthetic error snapshot after the timeout, matching the legacy
  behavior.

### Integration points

`routes/+page.svelte` configures the orchestrator via
`configureBattlePollingHandlers` and `configureMapPollingHandlers`:

* `onBattleComplete`, `onAutoAdvance`, and `onDefeat` delegate to the existing
  room advancement helpers and defeat overlay.
* `onBattleError` and `onMissingSnapshotTimeout` surface lightweight error
  overlays while forcing a map refresh.
* `onRunEnd` tears down local state, mirroring the legacy
  `shouldHandleRunEndError` guard.
* The map handler’s `onBattleDetected` callback ensures the battle poller runs
  immediately after `getMap` detects a combat room without waiting for the next
  UI state tick.

Manual halts (`setManualSyncHalt(true)`) still pause all pollers. When a run is
ended from Settings or defeat handling, the root page calls
`stopBattlePolling()`, `stopMapPolling()`, and `stopUIPolling()` before clearing
`runStateStore` so no timers survive the teardown.

Rooms that return `awaiting_next = true` without rewards continue to auto-advance
through `handleNextRoom()`. Because the battle controller now owns the cadence,
the map poller resumes immediately after advancement, keeping room headers and
map metadata synchronized for subsequent actions.
