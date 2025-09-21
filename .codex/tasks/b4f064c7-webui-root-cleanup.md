Coder, refactor the WebUI root page and retire legacy component naming.

## Context
- `frontend/src/routes/+page.svelte` has ballooned to 1,500+ lines and mixes data fetching, polling orchestration, overlay wiring, and UI state normalization in a single Svelte component, making it difficult to reason about and test.【09b46a†L1-L2】
- The file still contains legacy helpers (e.g., the "NEW UI API APPROACH" block, manual polling, and direct `window.*` flags) intermixed with current run handling, making cleanup risky without a structured split.【F:frontend/src/routes/+page.svelte†L1290-L1455】
- `frontend/src/lib/components/BattleReview.svelte` imports `LegacyFighterPortrait`, a name that implies it is deprecated even though it powers the modern review overlay.【F:frontend/src/lib/components/BattleReview.svelte†L1-L18】
- The corresponding component file `frontend/src/lib/battle/LegacyFighterPortrait.svelte` still carries TODO comments about future behavior and ships duplicated HP/overheal logic that also lives in `BattleFighterCard.svelte`.【F:frontend/src/lib/battle/LegacyFighterPortrait.svelte†L1-L80】

## Requirements
- Break `+page.svelte` into focused modules: extract run state management, backend polling, and overlay coordination into dedicated stores/utilities under `frontend/src/lib/systems/`. Keep the Svelte page focused on composing the viewport and wiring events.
- While refactoring, remove vestigial logic such as the direct `window.af*` flags and the commented "NEW UI API" scaffolding, replacing them with explicit stores that can be unit tested.
- Replace `frontend/src/lib/battle/LegacyFighterPortrait.svelte` with a modernized review portrait that reuses the shared fighter card helpers, then delete the legacy component outright once call sites are migrated.
- Update all imports (`BattleReview.svelte`, any other references) and ensure styles/tests/docs reference the new portrait module and utilities.
- Refresh documentation under `frontend/.codex/implementation/battle-review-ui.md` (and related notes) to describe the new module boundaries and the retirement of the legacy portrait file.

## Notes
- Add targeted unit or component tests for the new extracted stores so regressions in run polling or overlay gating are caught quickly.
- Coordinate with other in-flight frontend work when renaming the portrait component to avoid merge pain (flag in PR description if necessary).

Task ready for implementation.
