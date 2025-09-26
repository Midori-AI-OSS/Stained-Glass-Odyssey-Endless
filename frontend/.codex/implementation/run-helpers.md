# Run Helpers

Root run state now lives in dedicated stores under `frontend/src/lib/systems/`. `routes/+page.svelte` mirrors the store values for template bindings, but the store mutators own run identifiers, party snapshots, room metadata, and battle flags.

- `frontend/src/lib/systems/runState.js`
  - `createRunStateStore(storage?)` tracks the active run identifier, selected party list, map rooms, current/next room metadata, `roomData`, `battleActive`, and the last battle snapshot. The root page now reads `$runState` for display state and routes party changes through the store mutators.
  - Exported helpers (`runState`, `runStateStore`, `loadRunState`, `saveRunState`, `clearRunState`) remain the primary way to access and persist run information. Because the store owns persistence, SSR runs and tests can inject fake storage safely while party IDs stay normalized and de-duplicated.
  - `setBattleActive` feeds the shared derived store consumed by overlay helpers and the polling orchestrator. Manual halts and overlay gating now rely on this derived signal rather than toggling standalone globals.

- `frontend/src/lib/systems/overlayState.js`
  - Centralizes reward/review overlay flags and manual polling halts. `overlayBlocking` reflects whether any overlay should pause backend polling, while `haltSync` adds manual halts to the derived signal.
  - Provides imperative APIs (`setRewardOverlayOpen`, `setReviewOverlayState`, `setManualSyncHalt`, `resetOverlayState`) for overlay hosts and menu flows.
  - Exports `battleActive` derived from `runStateStore` so indicators like `PingIndicator.svelte` and `BattleView.svelte` can render combat status without reading globals.

- `frontend/src/lib/systems/uiApi.js`
  - Remains the primary UI-centric API for starting runs, performing room actions, advancing rooms, updating parties, fetching battle data, and selecting rewards.
  - `handleFetch` normalizes backend errors and reports them through the overlay system. `advanceRoom` reads the current run state before sending actions to avoid skipping pending rewards.

- `frontend/src/lib/systems/pollingOrchestrator.js`
  - Owns the UI state, battle snapshot, and map fallback cadences. The controller subscribes to `haltSync`, `overlayBlocking`, and the overlay view store so all loops pause while overlays are active or manual halts are engaged.
  - Exposes `rootPollingController`, `battlePollingController`, `mapPollingController`, and helper utilities (`startUIPolling`, `stopUIPolling`, `syncUIPolling`, `syncBattlePolling`, `syncMapPolling`, plus configuration setters). `+page.svelte` configures callbacks for overlays, auto-advance, and defeat handling and relies on the controller to resume polling after each event.
  - Implements exponential backoff on repeated failures and automatically falls back to `getMap` when UI polling stalls, eliminating the bespoke timers that previously lived in the root page.

- UI entry points
  - `frontend/src/routes/+page.svelte` mirrors `$runState` for template bindings and forwards all mutations through the store. Polling start/stop logic now delegates to the orchestrator controllers so cadence stays centralized.
  - `frontend/src/lib/components/RunButtons.svelte` continues to expose `buildRunMenu`, while `NavBar.svelte` surfaces in-run actions (inventory, editor, settings). These components now rely on the shared stores for battle gating instead of global flags.

- Settings & utility modules
  - `frontend/src/lib/systems/api.js`: `getBackendFlavor()` reports the active backend flavor so the root page can surface maintenance overlays.
  - `frontend/src/lib/systems/runErrorGuard.js`: `shouldHandleRunEndError` coordinates with run state helpers to decide when to halt polling and surface defeat dialogs.

When adding new run-related helpers, prefer colocating them in `frontend/src/lib/systems/` alongside the stores and update this document accordingly.
