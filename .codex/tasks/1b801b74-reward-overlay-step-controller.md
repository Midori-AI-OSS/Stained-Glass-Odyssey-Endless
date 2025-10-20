# Implement reward overlay phase controller

## Summary
Umbrella pointer for the frontend controller track. Work has been split so coders can land the state machine, drops-only phase, advance countdown, and resilience pieces independently.

## Subtasks
- `.codex/tasks/f7ae6ddd-reward-overlay-state-machine.md` — build the state machine scaffold around `reward_progression`.
- `.codex/tasks/01508135-drops-phase-overlay-refactor.md` — render the Drops-only experience.
- `.codex/tasks/bcfc52bc-reward-advance-countdown.md` — add the advance button and countdown timer.
- `.codex/tasks/6afb12ae-reward-overlay-resilience.md` — harden transitions and accessibility edge cases.

## Notes
- Keep this parent file updated as subtasks land or new gaps appear.
- Coordinate sequencing with the card/relic refresh umbrella to avoid merge conflicts in shared components.
