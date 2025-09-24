Coder, extract the run state and polling orchestration out of `frontend/src/routes/+page.svelte`.

## Context
- `frontend/src/routes/+page.svelte` is ~1,500 lines and mixes run state, polling timers, overlay triggers, and viewport wiring, making the entry point fragile to touch.【F:frontend/src/routes/+page.svelte†L1-L80】【F:frontend/src/routes/+page.svelte†L1290-L1455】
- The file still flips legacy globals (`window.af*`) and carries the abandoned "NEW UI API" helpers, so state transitions and feature flags are opaque to contributors.【F:frontend/src/routes/+page.svelte†L340-L520】

## Requirements
- Create focused stores/utilities under `frontend/src/lib/systems/` for (a) active run state, (b) backend polling + retry management, and (c) overlay gating so the page component simply wires them into the viewport tree.
- Replace the `window.af*` flags and commented "NEW UI API" block with explicit store APIs that encapsulate the same lifecycle behavior and can be unit tested.
- Update `+page.svelte` to import and use the new stores, trimming the component to presentation logic and event handlers.
- Ensure existing overlays and viewport initialization still work by covering the new stores with targeted unit tests (e.g., polling retry cadence, overlay gating transitions).
- Add transition notes to `frontend/.codex/implementation/battle-review-ui.md` (or a new root-page doc) describing the new modules and the retirement of the inline helpers.

## Notes
- Coordinate with other frontend efforts touching the root page to avoid merge conflicts; document any required follow-up tasks for remaining subtrees that still need extraction.
