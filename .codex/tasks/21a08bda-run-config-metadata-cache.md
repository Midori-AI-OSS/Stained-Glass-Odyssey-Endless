# Task: Cache run configuration metadata and surface recent modifier presets

## Background
The new run startup wizard fetches `/run/config` metadata on every visit and clears modifier selections once a run launches. The goal file `33e45df1-run-start-flow.goal` calls for persisting the metadata and exposing recently used modifier presets so returning players can resume quickly without hammering the backend.

## Objectives
- Avoid redundant `GET /run/config` requests within a session by caching the payload alongside its metadata hash and automatically refetching when the hash changes.
- Persist the last few modifier configurations locally (per run type) and expose them as quick-start presets in the modifier step of the wizard.

## Deliverables
- Frontend implementation that memoizes the configuration metadata for the duration of the session, clears it only when the backend hash changes, and gracefully handles fetch failures.
- UI affordance in `RunChooser` that lists the most recent modifier presets (e.g., last 3 per run type), including stack selections and reward previews, letting players reapply them with one click.
- Telemetry updates (if needed) to distinguish quick-start preset usage from manual configuration adjustments.
- Unit and/or UI test updates proving that cached metadata prevents duplicate fetches and that preset selections persist and reapply as expected.

## References
- `.codex/tasks/33e45df1-run-start-flow.goal`
- `frontend/src/lib/components/RunChooser.svelte`
- `frontend/src/lib/systems/uiApi.js`
- `frontend/tests/run-wizard-flow.vitest.js`
- `backend/routes/ui.py`
