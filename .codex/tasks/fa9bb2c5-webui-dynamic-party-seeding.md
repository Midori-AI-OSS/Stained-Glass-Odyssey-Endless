Coder, replace the hard-coded `'sample_player'` party seed with roster-driven initialization.

## Context
- The root page still pushes `['sample_player']` into the party store before real roster data loads, leaking a fake id into new runs until a user reselects a roster member.【F:frontend/src/routes/+page.svelte†L30-L39】

## Requirements
- Update the party initialization flow to wait for real roster metadata (e.g., `getPlayers()`), then seed the party with the first available player id or leave it empty until the user selects one.
- Ensure persisted runs that were created while the placeholder existed continue to load by migrating or validating saved parties on hydration.
- Cover the new behavior with unit/component tests that confirm no placeholder id leaks into new runs and persisted parties hydrate correctly.
- Document the new initialization rules in `frontend/.codex/implementation/party-ui.md` and any related onboarding notes.
- Provide acceptance notes in your PR description that spell out the QA steps for verifying party seeding (fresh run, persisted
  run, and empty roster scenarios) so the review team can validate the metadata-driven flow.

## Notes
- Coordinate with backend developers if additional metadata is needed to determine the default selection logic.
