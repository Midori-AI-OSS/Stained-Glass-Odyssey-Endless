# Add coverage for four-phase reward flow

## Summary
Back the four-phase reward overlay redesign with automated checks that confirm Drops → Cards → Relics → Review sequencing and the new interaction affordances.

## Requirements
- Add frontend tests (Vitest + Svelte Testing Library) that simulate the phased flow:
  - Drops phase renders loot-only UI and counts down to auto-advance after 10 s (mock timers to avoid delays).
  - Cards phase highlights on first click, exposes the confirm button, and confirms on second click or Enter/Space.
  - Relic phase mirrors card behaviour and clears highlights when the backend payload clears staging.
  - Battle review launches only when the setting is enabled.
- Extend idle-mode automation tests/mocks (if present) so they verify automation still confirms staged rewards under the new flow.
- Provide utility selectors/mocks to simplify staged reward payload assertions in tests.

## Dependencies
- Implement the four-phase overlay task (`5e4992b5-reward-flow-four-step-overhaul.md`).

## Out of scope
- Backend contract tests; focus on frontend behaviour.

