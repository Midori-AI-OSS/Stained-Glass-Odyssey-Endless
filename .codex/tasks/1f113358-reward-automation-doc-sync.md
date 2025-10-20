# Align reward automation & docs with four-phase flow

## Summary
Update idle-mode automation, regression tests, and documentation so they follow the new four-step reward overlay sequence.

## Requirements
- Adjust idle automation scripts/services to advance through the Drops, Cards, Relics, and Battle Review phases, invoking the new confirm hooks introduced by the overlay refresh.
- Add or update automated tests to cover the countdown auto-advance, manual advance button, and confirm flows for cards and relics.
- Review any mocked data or fixtures to ensure they include representative `reward_progression` metadata so tests don’t regress.
- Update `frontend/.codex/implementation/reward-overlay.md` with the four-phase sequence, wiggle interaction, countdown advance behaviour, and removal of the preview panel.
- Coordinate with backend reviewers to confirm no API adjustments are required; document any assumptions or follow-up backend work in the task file if discovered.

## Coordination notes
- Check `.codex/review` and `.codex/planning` for related automation efforts to avoid duplicating work.
- Work with QA to validate the automation on staging once UI changes land.
