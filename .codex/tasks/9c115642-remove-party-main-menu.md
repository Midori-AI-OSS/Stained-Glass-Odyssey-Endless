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
