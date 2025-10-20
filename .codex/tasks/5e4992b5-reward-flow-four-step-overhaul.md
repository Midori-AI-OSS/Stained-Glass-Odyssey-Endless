# Rebuild reward overlay into four-phase flow

## Summary
Umbrella pointer for the reward overlay overhaul. The monolithic work item has been decomposed into focused umbrellas, each of which now references bite-sized implementation tasks so coders can land the Drops → Cards → Relics → Review experience incrementally.

## Subtasks
- `.codex/tasks/1b801b74-reward-overlay-step-controller.md` — controller umbrella.
  - `.codex/tasks/f7ae6ddd-reward-overlay-state-machine.md`
  - `.codex/tasks/01508135-drops-phase-overlay-refactor.md`
  - `.codex/tasks/bcfc52bc-reward-advance-countdown.md`
  - `.codex/tasks/6afb12ae-reward-overlay-resilience.md`
- `.codex/tasks/b500ea24-card-relic-confirmation-refresh.md` — card/relic UX umbrella.
  - `.codex/tasks/ebfb0389-card-highlight-wiggle.md`
  - `.codex/tasks/d7196ce9-relic-highlight-confirm.md`
  - `.codex/tasks/1f2b8b4a-reward-confirm-accessibility.md`
- `.codex/tasks/1f113358-reward-automation-doc-sync.md` — automation + docs umbrella.
  - `.codex/tasks/68168a61-reward-automation-advance-hooks.md`
  - `.codex/tasks/b8904271-reward-regression-coverage.md`
  - `.codex/tasks/2d6e3f12-reward-overlay-docs-update.md`

## Notes
- Use this parent file to coordinate sequencing and cross-task dependencies.
- Revisit once all subtasks close to confirm no follow-up umbrella work remains.
