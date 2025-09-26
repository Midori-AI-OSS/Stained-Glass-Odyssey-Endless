Coder, replace the root-page overlay gating globals with dedicated overlay state helpers and clean up legacy UI API remnants.

## Context
- Overlay suppression logic is spread across `+page.svelte`, gating actions and polling with `window.afRewardOpen` / `window.afReviewOpen` checks instead of a structured store.【F:frontend/src/routes/+page.svelte†L608-L823】【F:frontend/src/routes/+page.svelte†L1402-L1494】
- The file still references the deprecated "NEW UI API" block and toggles globals like `window.afHaltSync` / `window.afBattleActive` for other components to detect, increasing coupling.【F:frontend/src/routes/+page.svelte†L1388-L1494】【F:frontend/src/routes/+page.svelte†L169-L174】

## Requirements
- Introduce overlay gating utilities or stores under `frontend/src/lib/systems/` that expose explicit APIs for reward/review overlays and battle-active signals (replacing `window.af*`).
- Update `+page.svelte` and any dependent helpers (`openOverlay`, battle polling) to use the new APIs so overlay state is derived from Svelte stores rather than globals.
- Remove the obsolete "NEW UI API" comment block after migrating the logic and document the new integration points inline or via module JSDoc.
- Provide Vitest coverage verifying that overlay openings pause/resume polling and battle indicators through the new store APIs.
- Coordinate with the run state and polling orchestrator tasks to ensure shared state (haltSync, battleActive) is sourced from the new helpers instead of window globals.

## Notes
- Capture any remaining legacy global usages in a follow-up list if they cannot be removed within this task.
