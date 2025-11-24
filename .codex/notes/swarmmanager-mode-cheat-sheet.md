# Swarm Manager Mode Cheat Sheet

## Session Summary
- Dispatched 10+ tasks through the Codex MCP tool while honoring the user's normal/low swarm-level restriction.
- Routed work up the chain: Auditor → Task Master → Coder, and captured handoffs for each specialist.
- Tracked git commits and pushes after meaningful work batches, while monitoring blockers and task file movements.

## Key Lessons Learned
1. **Always start with the cheat sheet.** `.codex/modes/SWARMMANAGER.md` documents every critical parameter and dispatch pattern; verify it before building a session.
2. **Respect swarm level constraints.** Normal/low only (no high/max) means choosing the right model for cost and reasoning depth while keeping approvals off.
3. **Git workflow is essential after each batch.** Run `git status`, stage everything with `git add -A`, commit with a descriptive `[TYPE]` message, and push to the current branch before moving on.
4. **Task file movements belong to Specialists.** Swarm Managers never move files between `wip`, `review`, or `taskmaster`; watch the folders and let the specialists handle transitions.
5. **Codex MCP tool parameters to mind:** always provide `cwd`, `model`, `config.reasoning-effort`, `approval-policy`, `sandbox`, and a clear `prompt`; capture the reasoning level per swarm setting.
6. **Gather context first.** Read every task file in full before dispatching so you can judge complexity, depth of reasoning, and the right swarm level.
7. **Batch related work.** Group similar tasks in one dispatch wave, then commit and push all results as a single atomic update to keep history clean.
8. **Stay branch-aware.** Confirm the current branch via `repoContext` (or equivalent) before launching work so pushes land where they belong.

## What Worked Well
- Leveraged the normal level for complex feature work such as ultimates and buff/debuff logic.
- Used the low level for documentation updates and straightforward fixes to keep costs down.
- Followed a sequential dispatch flow: Auditor → Task Master → Coder, which kept responsibilities clear.
- Committed and pushed after each meaningful work batch to solidify progress and unblock the next steps.
