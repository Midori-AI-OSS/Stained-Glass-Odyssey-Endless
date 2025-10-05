# Task: Polish Run Modifier Wizard UX

## Summary
Audit and update the Run Setup wizard so every modifier uses the backend metadata to surface complete tooltip copy, reward previews, and consistent stacking messaging, while ensuring the Configure Modifiers step layout matches other panels and avoids unnecessary scroll bars.

## Why
The run configuration goal calls out that modifier metadata ships rich semantics, but the wizard does not yet surface consistent tooltips or layout polish. Addressing this UX debt is a prerequisite before wiring modifiers into gameplay because players need to understand how their selections behave.

## Requirements
- Cross-check `RunChooser.svelte` against the metadata schema in `run_configuration.py` and ensure each modifier row renders:
  - Tooltip text that explains the default unlimited stacking rules alongside reward/diminishing info from `preview` / `effects` fields.
  - Reward preview chips that mirror the backend preview math, including uncapped stacks.
- Stretch the Configure Modifiers step container to fill the panel height so the primary call-to-action stays anchored; scrolling should only appear when content truly overflows.
- Keep modifier selections persisted in local storage exactly as today; new tooltip/preview data must hydrate from the fetched metadata without introducing extra requests.
- Document any new helper utilities in the component or adjacent UI API modules.

## Acceptance Criteria
- Modifier tooltips reinforce that stacks are uncapped per the global design rule and read their copy directly from metadata fields so they stay in sync with backend expectations.
- Modifier tooltips and reward previews reflect the numbers defined in the metadata preview blocks for at least three sample modifiers (covering foe-focused, player-penalty, and economy tags).
- The Configure Modifiers view no longer shows an always-on scrollbar at default window sizes in Storybook and the in-app wizard; the CTA remains fixed at the bottom of the panel until real overflow occurs.
- Frontend tests (`run-wizard-flow.vitest.js`) updated or extended to cover the tooltip copy and layout regressions if applicable.

## References
- Frontend wizard component: `frontend/src/lib/components/RunChooser.svelte`
- Backend metadata schema: `backend/services/run_configuration.py`
- Existing flow coverage: `frontend/tests/run-wizard-flow.vitest.js`
