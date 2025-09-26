Writer, capture the root-page state modularization follow-up documentation and integration checklist.

## Context
- Splitting run state, polling, and overlay globals into dedicated modules will change how contributors initialize the root viewport and battle review flows.【F:frontend/src/routes/+page.svelte†L33-L62】【F:frontend/src/routes/+page.svelte†L1388-L1494】
- Existing implementation notes live in `frontend/.codex/implementation/battle-review-ui.md`, but they still describe the monolithic `+page.svelte` helpers and legacy window globals.【F:frontend/.codex/implementation/battle-review-ui.md†L1-L120】

## Requirements
- Draft updated documentation (extend `frontend/.codex/implementation/battle-review-ui.md` or add a sibling doc) describing the new run-state store, polling orchestrator, and overlay helpers along with their integration touchpoints.
- Include a migration checklist for coders touching `+page.svelte`, indicating which module owns player restoration, overlay gating, and battle lifecycle hooks after modularization.
- Enumerate any QA steps or smoke tests needed after the refactor (e.g., reward overlay still pausing polling, run resume from storage) so Task Masters can attach them to future tasks.
- Coordinate with the coders executing the modularization tasks to ensure the documentation reflects the final API names and public contracts.

## Notes
- Attach links or references to the new task IDs (`6a8ad619`, `e0ef9019`, `f152ac25`) so the work stays discoverable in planning reviews.

Progress update (2025-09-29): Clarified documentation to match the current implementation—UI polling orchestrator coverage, overlay gating helpers, and outstanding run-state store migration work remain called out for future follow-up. Additional edits pending once the run store fully replaces local root-page state.
Progress update (2025-09-30): Updated the run helper reference to remove claims about the root page deferring to the store and the orchestrator owning a `getMap` fallback. Further revisions will land alongside the actual state migration.
