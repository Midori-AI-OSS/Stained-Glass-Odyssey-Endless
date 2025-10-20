# Rebuild reward overlay into four-phase flow

## Summary
Umbrella pointer for the reward overlay overhaul. The original monolithic work item has been decomposed into three focused tasks so coders can deliver the Drops → Cards → Relics → Review experience incrementally.

## Subtasks
- `.codex/tasks/1b801b74-reward-overlay-step-controller.md` — introduce the explicit four-phase controller, drops-only screen, and timed advance button.
- `.codex/tasks/b500ea24-card-relic-confirmation-refresh.md` — refresh card/relic selection with wiggle animation, on-card confirms, and shared stained-glass styling.
- `.codex/tasks/1f113358-reward-automation-doc-sync.md` — update idle automation, regression coverage, and documentation to follow the new flow.

## Notes
- Use this parent file to coordinate sequencing and cross-task dependencies.
- Revisit once all subtasks close to confirm no follow-up umbrella work remains.
