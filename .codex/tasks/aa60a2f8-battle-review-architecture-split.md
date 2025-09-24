Coder, re-architect the Battle Review UI around modular stores and timeline-first components.

## Context
- `frontend/src/lib/components/BattleReview.svelte` currently glues together summary fetches, overlays, and tables inside a single component, making it difficult to add advanced views.【F:frontend/src/lib/components/BattleReview.svelte†L1-L200】【F:frontend/src/lib/components/BattleReview.svelte†L340-L520】
- Existing docs still describe the legacy three-column layout that relied on `LegacyFighterPortrait` and lacked timeline playback.【F:frontend/.codex/implementation/battle-review-ui.md†L1-L13】

## Requirements
- Extract data handling into stores/utilities under `frontend/src/lib/systems/battleReview/` covering summaries, events, derived metrics, and overlay lifecycle.
- Split the UI into focused components (tabs shell, timeline region, per-entity table container, events drawer) that consume the new stores, replacing the monolithic `BattleReview.svelte` composition.
- Introduce the timeline-first layout framework (metric tabs over a timeline viewport with side panels) without yet implementing advanced interactions such as comparisons or pins.
- Ensure reduced-motion preferences propagate through the new components (disable animations/transitions where required) and document the handling in the relevant implementation notes.
- Add component/unit tests that validate the stores' data shaping and the shell layout rendering.

## Notes
- Coordinate with the portrait modernization work so the new layout consumes the updated portrait components.
