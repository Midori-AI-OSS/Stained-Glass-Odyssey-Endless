# Reconcile `⚠️ PARTIAL` Loader Note in Action Plugin GOAL

## Priority
Normal

## Owner
@action-system-lead

## Background
The `.codex/tasks/wip/GOAL-action-plugin-system.md` file currently carries a `⚠️ PARTIAL` loader note that hints at open questions around action auto-discovery. We need to reconcile that uncertainty before declaring the loader stable.

## Request
Owning the action system, please resolve the open loader questions by producing:

1. **Checklist of outstanding auto-discovery edge cases** — list each scenario that still needs coverage (e.g., nested directories, dark-mode plugins, non-standard naming, etc.) so we can confirm whether auto-discovery already handles them or needs adjustments.
2. **Code references and validation steps** — cite the exact files or loader functions that must be examined/updated and name the tests (unit, integration, or manual steps) to run to prove auto-discovery works correctly.

## Clarifying Deliverables
- Provide a concise checklist (two to four bullets) of unresolved or fragile auto-discovery edge cases that still trigger the `⚠️ PARTIAL` warning.
- For each case, note whether it is handled today or requires follow-up, and link it to the code location responsible.
- Enumerate specific tests or scripts to execute (with commands or test names) that validate auto-discovery before removing the warning.

## Follow-Up
Once the checklist and validation steps are satisfied, update the `GOAL-action-plugin-system.md` loader note to reflect the reconciled status or remove the warning if it is no longer relevant.
