Coder, move the backend polling and retry cadence out of `frontend/src/routes/+page.svelte` into a reusable orchestrator module.

## Context
- The page component manages timers for UI state polling, battle polling, and retry delays inline, guarded by `haltSync` flags and manual `setTimeout` juggling.【F:frontend/src/routes/+page.svelte†L48-L61】【F:frontend/src/routes/+page.svelte†L1392-L1495】
- Global overlays pause polling via `window.afRewardOpen` / `window.afReviewOpen` checks scattered through the polling helpers, making it difficult to test sync pauses or changes to cadence.【F:frontend/src/routes/+page.svelte†L1402-L1494】

## Requirements
- Create a polling controller under `frontend/src/lib/systems/` that exposes start/stop controls for UI state and battle polling, including retry backoff and overlay-aware gating.
- Centralize timer handling (request scheduling, cancellation, exponential backoff on errors) within the controller so the page only subscribes to status updates and dispatches commands.
- Replace the inline timers in `+page.svelte` with imports from the new controller, ensuring `haltSync` or equivalent pause logic still propagates to polling.
- Provide Vitest coverage that simulates overlay gating, retry delays, and halt/resume flows.
- Export typed events or stores from the controller so other components can observe polling status (last tick time, consecutive failures) without touching DOM globals.

## Notes
- Coordinate with the run state extraction to decide which module owns `haltSync` and related flags; document any shared contracts in the tests or module JSDoc.
