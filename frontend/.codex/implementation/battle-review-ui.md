# Battle Review Timeline Shell

The Battle Review overlay is now organized around a timeline-first layout backed by modular stores.

## Architecture Overview

- **State management** lives in `frontend/src/lib/systems/battleReview/state.js`. The exported `createBattleReviewState` helper fetches summaries and events, tracks loading status, derives overview metrics, and exposes the active tab/timeline data. Components access the state via the shared `BATTLE_REVIEW_CONTEXT_KEY` context.
- **`BattleReview.svelte`** sets up the state and renders the high-level header. It also owns the event-log toggle and pushes the state object into context for child components.
- **`TabsShell.svelte`** renders the metric tabs and composes the grid for the timeline viewport and per-entity metrics panel. The tab chips use `BattleReviewFighterChip.svelte`, which wraps the modern `BattleFighterCard` portrait so the battle review can share the same glow, motion, and cycling behaviors without maintaining a separate clone.
- **`TimelineRegion.svelte`** renders battle events as a multi-lane timeline. Markers are positioned by timestamp, grouped into damage/healing lanes, and include inline metadata for card plays and relic triggers. The component still consumes the derived `timeline` store so it can update reactively once events finish streaming from the backend.
- **`EntityTableContainer.svelte`** handles both the overview aggregate presentation and the entity-specific breakdowns. It renders a stats side panel in addition to the central metrics tables to keep the new "side panel" design consistent with the timeline-first layout.
- **`EventsDrawer.svelte`** shows the raw event log when toggled. It subscribes to `eventsOpen` and lazily loads events when the drawer opens.

The timeline-first grid places metric tabs across the top, the timeline viewport on the left, and entity metrics/side panels on the right. The layout collapses gracefully for smaller viewports.

### Battle Review Menu Overlay (Archive Access)

- **`BattleReviewMenu.svelte`** lives under `frontend/src/lib/components/battle-review/` and provides an archive view that can be opened from the main run menu. The overlay is mounted when `$overlayView === 'battle-review-menu'` and is rendered directly inside an `OverlaySurface` (no popup chrome) so the embedded review can stretch to the viewport edges.
- The menu fetches `/tracking/runs` and `/tracking/runs/<run_id>` through new helpers exported from `frontend/src/lib/systems/uiApi.js` (`listTrackedRuns`, `getTrackedRun`). While either request is in flight the menu shows a `TripleRingSpinner`, mirroring the rest of the overlay loading states.
- `groupBattleSummariesByFloor` normalizes each run's ordered `battles` payload (legacy responses may still use `battle_summaries`). Floors increment whenever a room index drops (floor reset), and the helper returns `{ floor, label, fights[] }` tuples so the menu can expose separate selects for run, floor, and fight. Tests in `frontend/tests/tracking-helpers.test.js` pin the grouping behavior.
- Once a fight is chosen the menu renders the existing `<BattleReview>` shell and passes the selected run ID and battle index. The embedded review inherits reduced-motion flags from the host overlay, so accessibility settings stay aligned with the core battle review experience.

## Shareable Logs Routing

- The Battle Review shell is also exposed as a standalone route at `/logs/[run_id]`. The page hydrates the review by parsing URL parameters (battle index, active tab, timeline filters, comparison selections, pins, and zoom window) with the helpers in `battleReview/urlState.js` and passing them to the shared stores.
- The route keeps the query string in sync with in-app changes by listening for the `statechange` event emitted from `BattleReview.svelte`. Navigation is performed with `goto(..., { replaceState: true })` so browser history stays tidy when filters change.
- The overlay now includes a **Copy Logs Link** button that serializes the current state into URL-safe params via `buildBattleReviewLink`. Links always target `/logs/[run_id]` and encode the tab, filters, comparison set, pins, and zoom range so the standalone page restores the same view.
- Reduced-motion and accessibility behavior match the in-game overlay by reusing settings from `motionStore` when the standalone route mounts and by mirroring the overlay header semantics.

## Reduced Motion Handling

- The store exposes a `reducedMotion` derived store based on incoming props. Components consult this store when handing off reduced-motion preferences to portrait subcomponents or transitions.
- Tabs and portraits avoid hover animations when reduced motion is requested, and the event drawer skips transition effects entirely.

## Skip Battle Review Setting

Players can bypass the Battle Review screen entirely by enabling the **Skip Battle Review** toggle in the Gameplay settings tab (see [`settings-menu.md`](settings-menu.md)). When this setting is active, the post-battle summary is skipped and the game automatically advances to the next room after battle completion.

## Root Page State Modularization (2025 Refactor)

Splitting the 1.5k-line `+page.svelte` root view into composable stores is an ongoing 2025 effort tracked by the modularization epic (`ab4ecf16`). The goal is to let overlays, battle review, and the standalone logs route observe battle state without reaching through DOM globals. Three modules anchor the refactor:

- **Run state store** — encapsulates persistence and normalization for run metadata so the page, overlays, and QA tooling can subscribe to a single source of truth.
- **Overlay gating store** — replaces the legacy `window.af*` flags with Svelte stores that gate polling and surface manual halts.
- **Polling orchestrator** — centralizes UI state polling cadence today, with battle snapshot integration planned for a follow-up.

### Run state store (`frontend/src/lib/systems/runState.js`)

- `createRunStateStore(storage?)` constructs a writable store that tracks the active run identifier, selected party roster, map rooms, current/next room metadata, the latest `room_data` payload, `battleActive`, and the last battle snapshot.
- Persistence helpers (`restoreFromStorage`, `persistRunId`, `clear`) wrap `localStorage` access and guard against SSR environments. Callers should prefer `loadRunState`, `saveRunState`, and `clearRunState` exported via `$lib`.
- Normalizers inside the store de-duplicate party IDs, clone map room entries to avoid shared references, and coerce boolean flags. This keeps downstream overlays from needing to defensive-copy backend payloads.
- `runStateStore.setBattleActive` mirrors the combat lifecycle into the shared overlay gating helpers, but the root page still toggles its local `battleActive` flag directly for now.
- The store currently powers helper utilities and tests, but `+page.svelte` still owns run metadata through local `let` declarations while migration work continues.
- **Integration touchpoints (in progress)**: overlays and tooling can read `runStateStore.getSnapshot()` when capturing review payloads. Future patches will wire backend responses through `runStateStore.applyUIState` and remove the local run state copies from `+page.svelte`.

### Overlay gating store (`frontend/src/lib/systems/overlayState.js`)

- `overlayStateStore` tracks `rewardOpen`, `reviewOpen`, `reviewReady`, and `manualHalt`. Derived helpers expose `overlayBlocking` (reward open or review open-and-ready), `haltSync` (manual halt OR blocking), and `battleActive` (mirrors `runStateStore.battleActive`).
- The module re-exports imperative helpers (`setRewardOverlayOpen`, `setReviewOverlayState`, `setManualSyncHalt`, `resetOverlayState`) so overlay hosts can respond to mount/unmount events without sharing DOM globals.
- `OverlayHost.svelte`, `PingIndicator.svelte`, and the settings cleanup flow already import these helpers; remaining references in `+page.svelte` should move to `$overlayState`/`haltSync` to finish the migration.
- **Integration touchpoints**: the polling orchestrator will subscribe to `haltSync` to pause retries, and the battle review overlay should call `setReviewOverlayState({ open: true, ready: false })` while loading snapshots to keep the UI consistent.

### Polling orchestrator (`frontend/src/lib/systems/pollingOrchestrator.js`)

- Responsible today for kicking and cancelling UI state (`getUIState`) polling loops. It exposes `startUIPolling`, `stopUIPolling`, and `syncUIPolling` helpers plus derived status/retry metadata.
- The controller subscribes to `haltSync` to pause retries when overlays block sync and publishes each payload through the shared `applyUIState` handler before legacy `+page.svelte` state updates.
- Battle polling (`startBattlePoll` / `pollBattle`) still lives inside `+page.svelte`. A future follow-up will migrate that loop once the battle poller is refactored to share the orchestrator cadence.
- Error handling mirrors the previous UI poller logic: an exponential backoff starting at 1s and doubling to a 30s ceiling.
- **Integration touchpoints**: `+page.svelte` triggers `startUIPolling` when a run begins/resumes and `stopUIPolling` when halting for overlays. Components can subscribe to the orchestrator's status stores, but no automatic `getMap` fallback exists yet.

### Migration checklist for contributors touching `+page.svelte`

1. (In progress) Replace direct `let` declarations for run metadata with subscriptions to `$runState` and call the corresponding `runStateStore.set*` helpers when backend payloads arrive.
2. Import `haltSync` and `overlayBlocking` from `$lib` instead of recomputing overlay conditions. Remove any remaining `overlayIsBlocking()` wrappers that reach into stores via `get()`.
3. (Future) Move battle polling timers into the orchestrator module so the page only coordinates start/stop signals for both UI state and battle snapshots.
4. Update reward/review overlays to toggle `overlayStateStore` instead of setting `window.af*` globals. Ensure manual sync halt flows call `setManualSyncHalt(true)` before opening long-lived overlays.
5. Adjust tests or mocks to exercise the new store APIs (see `frontend/tests/run-state-store.test.js` for reference).

### QA & Smoke Test Checklist

- Resume an in-progress run from `localStorage` and confirm map/party data hydrates correctly (covers `runStateStore.restoreFromStorage`).
- Trigger a reward overlay mid-run; verify polling pauses (`haltSync` becomes `true`) and resumes after the overlay closes.
- Complete a battle and open the Battle Review overlay; ensure `battleActive` flips to `false` and the review overlay receives the cached snapshot.
- Scrub the battle timeline while switching entity/type filters. Confirm that markers track card plays, relic triggers, damage bursts, and healing events in chronological order. Highlighted events should update when focusing a specific party member or foe.
- Force a polling error (e.g., disconnect backend) and confirm the orchestrator retries UI polling with backoff and surfaces errors through the shared status store.
- Run `bun test frontend/tests/run-state-store.test.js` and, once implemented, the future battle polling controller spec whenever the stores change.

### Task references

- `6a8ad619-webui-run-state-store`
- `f152ac25-webui-overlay-gating`
- `e0ef9019-webui-polling-orchestrator`
- `05990b91-webui-root-state-transition-docs`
