# Fix PartyPicker roster scrolling and add gradient fades

## Problem
When players open the PartyPicker via the run-start flow with a large roster, the entire overlay grows taller than the viewport. The browser ends up scrolling the full window instead of keeping the menu pinned, and the Party roster header jumps off screen. QA also reported the lack of any visual affordance that more characters are available beyond the fold.

## Why this matters
* The roster list in `frontend/src/lib/components/PartyRoster.svelte` already uses `overflow-y: auto`, but container sizing and flex rules in `PartyPicker.svelte` and `MenuPanel.svelte` allow the overlay to expand vertically, breaking the modal illusion.
* Scrolling the whole page can expose background elements and causes focus loss for keyboard/gamepad users, which is a regression from the intended single-column PartyPicker layout.
* Without fade indicators at the top and bottom of the roster column, players may not realize more characters exist off-screen, especially after we remove the redundant Party entry elsewhere in the UI.

## Requirements
* Constrain the PartyPicker overlay so only the roster column scrolls:
  * Audit the grid/flex sizing in `frontend/src/lib/components/PartyPicker.svelte` and ensure the left column with `<PartyRoster>` honors a max height tied to the MenuPanel viewport.
  * If the issue originates from `MenuPanel.svelte` (e.g., missing `min-height: 0` or overflow handling), patch it so the modal container remains fixed while inner regions scroll independently.
* Update `PartyRoster.svelte` to keep the Party header, sort controls, and inline divider pinned while the list of characters scrolls beneath them.
* Add subtle top/bottom gradient fades inside the scrolling region to hint at additional content. Reuse existing color tokens where possible so the fades match the glass UI.
* Verify the compact roster variant (used in overlays like the Combat Viewer and minimized layouts) still renders correctly without inheriting the fades or scroll constraints.
* Cover the change with at least one frontend test:
  * Extend an existing Vitest/Playwright test or add a new component-level test under `frontend/tests/` that mounts `PartyPicker` with >12 characters and asserts the scroll container height stays within the viewport and the gradient elements render.
* Document the updated behavior:
  * Append a note to `.codex/implementation/party-ui.md` outlining the roster scroll constraints and gradient indicators.
  * Update any run-start UX notes in `.codex/instructions/main-menu.md` or related planning docs if they reference the previous scrolling quirk.

## Definition of done
* Opening PartyPicker with a large roster keeps the overlay anchored; only the roster list scrolls while the Party header remains visible.
* Top and bottom fades render when the roster overflows and disappear when the list fits without scrolling.
* Automated coverage captures the scroll container behavior, and the documentation describes the new layout.

---

## Status Update (Luna)

Tested by the lead dev: This task was not done right as there is no scrolling for the roster side... We made need to rescope as thats not the issue, Ill ask a coder to see if I can fix it with them. This update seems to have made the battle review screen stop working...

---

## Status Update (Nova)
- Scoped overflow to the PartyPicker grid so the overlay caps to the viewport while the roster column manages scrolling.
- Reworked `PartyRoster` layout to keep the selected party pinned and allow the roster list to scroll independently.
- Reverted unrelated `MenuPanel` sizing changes after confirming other overlays rely on the original behavior.

## Audit Notes (Auditor)
- `bun x vitest run tests/party-picker-scroll.vitest.js` aborts with an "Unknown Error: [object Object]" before loading any test files, so the newly added coverage never executes. Investigate and fix the Vitest environment so the roster scroll regression test can actually run.

## Status Update (Coder — 2025-02-18)
- Downgraded `@sveltejs/vite-plugin-svelte` to 5.0.0 and added a `browser` resolve condition so Vitest exercises the client runtime without aborting.
- Hoisted roster fixtures in the Vitest suite and verified gradients/scrolling by running `bun x vitest run tests/party-picker-scroll.vitest.js`.
- Updated `.codex/implementation/party-ui.md` and `.codex/instructions/main-menu.md` to describe the locked overlay and gradient hints.

ready for review — Vitest now runs `tests/party-picker-scroll.vitest.js` cleanly, the roster column remains the only scrolling region, and gradients signal overflow.
