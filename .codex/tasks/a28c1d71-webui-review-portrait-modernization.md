Coder, replace the legacy battle review portrait implementation with the shared fighter card primitives.

## Context
- `frontend/src/lib/components/BattleReview.svelte` still imports `LegacyFighterPortrait`, signaling the component is a stopgap despite powering the modern overlay.【F:frontend/src/lib/components/BattleReview.svelte†L1-L40】
- `frontend/src/lib/battle/LegacyFighterPortrait.svelte` duplicates HP/overheal logic that already lives in the battle fighter card components and carries TODOs about future behavior.【F:frontend/src/lib/battle/LegacyFighterPortrait.svelte†L1-L80】

## Requirements
- Build a new portrait component (e.g., `ReviewFighterPortrait.svelte`) that reuses the shared fighter card helpers for HP, overheal, and status effects.
- Update `BattleReview.svelte` and any other call sites to render the new portrait component and delete `LegacyFighterPortrait.svelte` once migration is complete.
- Align styles so the review overlay keeps its current layout while relying on the shared primitives; document any design adjustments required by the shared components.
- Add component tests to cover the new portrait rendering states (overheal, death, mimic) and guard against regressions.
- Refresh `frontend/.codex/implementation/battle-review-ui.md` (and related notes) to describe the new portrait component and the elimination of the legacy file.

## Notes
- Coordinate with the root page modularization task so portrait imports stay consistent during the refactor sequence.
- Explicitly flag the portrait component rename/migration in your PR description so reviewers and QA know to double-check the
  updated import paths and snapshots.
