# Harden reward overlay transitions & accessibility

## Summary
Tighten the reward overlay's transition handling, fallback behaviour, and focus management so each phase change remains resilient even when metadata is missing or users advance early.

## Requirements
- Implement guards around each phase entry to catch malformed `reward_progression` data and gracefully default to the legacy single-phase overlay with logging.
- Ensure early confirmations (manual button clicks, keyboard Enter) dispatch safe transitions and cannot fire multiple times or leave the overlay in a stuck state.
- Add focus management so the advance button gains focus when it appears, returns focus to the overlay root when auto-advancing, and respects skip paths.
- Verify screen reader announcements describe the new phase on entry and the countdown status for accessibility compliance.
- Document any remaining risks or follow-up work directly in the task file for visibility.

## Coordination notes
- Pair with QA or accessibility reviewers to validate screen reader messaging.
- Sync with backend engineers if additional metadata is required to cover new edge cases uncovered during implementation.
- Remaining risk: the Bun test runner currently resolves Svelte's server build, so reward overlay component tests must run under a DOM-capable environment (e.g., jsdom) to execute successfully.

ready for review
