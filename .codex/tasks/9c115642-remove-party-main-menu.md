# Remove standalone Party entry from the main menu

## Problem
The home screen currently advertises a dedicated “Party” entry in both the top navigation bar and the right-hand action list. Opening it duplicates the run-start overlay without providing any additional context, so the extra button feels redundant and confuses players about when party edits are needed.

## Why this matters
* `frontend/src/lib/components/NavBar.svelte` and `RunButtons.svelte` expose the PartyPicker overlay in multiple places, leading to duplicate affordances that distract from the Run flow.
* Documentation in `frontend/README.md` and `.codex/implementation/main-menu.md` still promises a Party tile, so the UX copy drifts further from reality each time the run-start overlay is refined.
* Removing the redundant entry simplifies the top-level menu and narrows QA coverage back to the Run button while keeping the party editor accessible when starting a run.

## Requirements
* Update `frontend/src/lib/components/NavBar.svelte` so the Users/Party icon no longer renders on the home screen. Ensure nearby keyboard navigation and spacing stay intact after the button is removed.
* Adjust `frontend/src/lib/components/RunButtons.svelte` to drop the Party item from `buildRunMenu`. Confirm the run panel still renders without layout gaps and no longer references the `handleParty` handler.
* Remove or refactor any remaining handlers in `frontend/src/routes/+page.svelte` (and related stores) that exist solely to support the redundant main-menu Party entry.
* Verify players can still edit their lineup when selecting **Run** (the Run chooser should still open the PartyPicker overlay before starting a run).
* Refresh documentation that mentioned the main-menu Party shortcut:
  * Update the “Main Menu actions” section in `frontend/README.md`.
  * Revise `.codex/implementation/main-menu.md` (and any linked overview docs) to reflect the streamlined action list.

## Definition of done
* The home screen shows no Party icon/button outside of the Run start flow, and keyboard/mouse navigation remains smooth.
* Clicking **Run** still opens the expected PartyPicker step before a run begins.
* Documentation describing the main menu no longer lists a standalone Party entry.

### Status notes (2025-10-27)
- Removed the nav-bar party button and right-rail menu entry; Run chooser still handles lineup edits.
- Updated frontend docs to reflect the streamlined main menu.
- Ran `bun test tests/settings-migration.test.js`; full suite currently fails at PullResultsOverlay string assertion.

### Audit notes (2025-10-28)
- Verified the nav bar and right-rail menu no longer expose a standalone Party entry and the Run flow still launches the PartyPicker overlay.
- `bun test` currently fails at `tests/stat-tabs-persistence.test.js` because `StatTabs.svelte` lacks the expected `context="module"` block.
- `.codex/implementation/main-menu.md` still documents the legacy Map/Edit/Craft/Stats layout instead of the current Run/Warp/Inventory/Battle Review/Guidebook/Settings roster, so the task's documentation update is incomplete.

### Status notes (2025-10-29)
- Updated `frontend/README.md` to describe the streamlined Run/Warp/Inventory/Battle Review/Guidebook/Settings lineup and added Discord/Website quick links.
- Revised `.codex/implementation/main-menu.md` and `.codex/instructions/main-menu.md` so documentation matches the current action column and removed Party shortcut.
- Replaced the obsolete StatTabs persistence test with coverage for the new upgrade overlay so `bun test tests/stat-tabs-persistence.test.js` runs cleanly.

### Audit notes (2025-02-15 – Auditor)
- Confirmed the top-left nav bar no longer renders a Party shortcut and still exposes Home/Inventory/Settings/Battle controls. Verified the right-rail menu now omits the Party entry while keeping the remaining Run, Warp, Inventory, Battle Review, Guidebook, and Settings actions plus quick links.
- Checked `+page.svelte` wiring to ensure no dead `handleParty` handler remains in the main menu pipeline and verified the Party overlay is still reachable from the Run flow only.
- Reviewed documentation updates across `frontend/README.md`, `.codex/implementation/main-menu.md`, and `.codex/instructions/main-menu.md` to confirm they describe the streamlined action list with quick links and no standalone Party entry.
- Validated the new `StatTabs` coverage exercises the upgrade overlay strings and dispatchers; `bun test tests/stat-tabs-persistence.test.js` now passes after `bun install`. `bun x vitest run tests/run-wizard-flow.vitest.js` still aborts with the existing "Unknown Error: [object Object]" before collecting tests.
- Environment setup: `uv sync` in `backend/` to provision the Python toolchain and `bun install` in `frontend/` before executing the test commands above.

requesting review from the Task Master
