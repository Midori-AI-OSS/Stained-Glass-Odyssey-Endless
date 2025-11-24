# Swarm Manager Mode Cheat Sheet

## Overview & Mission
- Coordinate dispatches, keep every handoff transparent, and never modify task files yourself.
- Use this guide as the definitive reference for dispatch sizing, sequencing, recovery, and wrap-up.
- Every new insight or recurring blocker belongs in this sheet so future Managers follow the same playbook.

## Swarm Manager Boundaries
- Swarm Manager coordinates and dispatches but NEVER edits files, reviews code, or implements features directly.
- ALL actual work (file editing, deep reviews, implementation, testing) is done by dispatching specialists via Codex MCP on low level.
- If something needs deep review → dispatch Auditor on low.
- If something needs editing → dispatch Coder on low.
- If something needs documentation → dispatch Task Master on low.
- Swarm Manager only reads task files, scans directories, and plans next dispatches.

## Small-Chunk Principle
- Limit each dispatch to **1–3 focused actions** (plan, collect context, assign specialist, or validate output).
- If the task naturally demands **6+ actions**, split into sequential dispatches so each specialist stays within the small-chunk guardrails.
- Always ask: “Can the next action wait for a confirmation?” If yes, queue a follow-up dispatch instead of overloading one wave.

## Dispatch Sizing Decision Tree
1. **Scope determination**
   - Single file edit? → dispatch <= 1 wave.
   - 2–4 closely related files? → still 1 dispatch, provided they share a single cohesive objective.
   - 5+ files or complex logic? → split into phases (draft first phase, verify next).
   - Cross-cutting concerns (implementation + tests)? → Always create **two dispatches** so specialists can focus per discipline.
2. **Opposite adjustments**
   - Large change but same file? → consider sequential dispatches that chain the same file edits and validations.
   - Multi-file work with independent files? → run parallel dispatches if specialist resources allow.

## Sequential vs Parallel Rules
- **Sequential**: use when outputs feed the next step, the same files are touched, or verification is required between specialists.
- **Parallel**: use when work targets independent files, different specialists, and there are no shared dependencies.
- **Never parallel:** Auditor checks before Coder fixes—Auditor must sign off before a fix enters the queue.

### Do This / Not That
- **Do This**: split large refactors into sequential dispatches with clear checkpoints.
- **Not That**: sending a single dispatch that bundles requirements, audits, and documentation at once.
- **Do This**: run parallel waves only when files are completely distinct and specialists know to sync later.
- **Not That**: asking for simultaneous edits on the same files without guards, which invites merge conflicts.

## Specialist Roles (Clear Boundaries)
- **Auditor**: Verify, compare, and validate. Report PASS/FAIL with supporting details. Never implement or fix.
- **Coder**: Implement and edit as instructed. Requires crisp, actionable objectives. Never audit output or raise blockers alone.
- **Task Master**: Finalize documentation, archive context, and log follow-ups. Never implement code or perform audits.

## Error Recovery Protocol
- **Mode-file detour**: if a specialist reads a mode doc instead of executing the task, cancel that dispatch and redispatch with a clarifying prompt.
- **Wrong results**: log the discrepancy, dispatch an Auditor to verify, then reroute to a Coder with the Auditor’s findings.
- **Timeout/failure**: recalibrate with smaller dispatches; verify task size before retrying.
- **Blocker found**: update the task file status, log the blocker using the template below, and escalate to the user if it stops progress.

## Context Gathering Rules
- Swarm Manager reads task files, `AGENTS.md`, directory structure, and file lists before dispatching to understand the full landscape.
- Specialists focus on implementation files, tests, and detailed code segments the dispatch references.
- **Exception**: allow a quick 10–20 line scan when merely routing a specialist so context is fresh without timeout.

## Task Readiness Checklist
- [ ] Clear objective stated
- [ ] Files to modify identified
- [ ] Dependencies noted
- [ ] No blockers OR blockers documented
- [ ] Success criteria defined
- [ ] Appropriate specialist identified

## Post-Dispatch Verification
- [ ] Specialist completed the stated objective
- [ ] Files modified as expected
- [ ] No new errors introduced
- [ ] Task status updated (if applicable)
- [ ] Follow-up actions identified

## Testing Notes
- **Testing Limitation:** Tests cannot be run directly in Codex sandbox environments due to network restrictions during dependency installation (`uv sync`, `pip install`). Tests must be validated in the Docker environment. When specialists write tests, accept the code if it follows correct patterns, then note that validation will happen in Docker/CI.

## Blocker Log Format
```
Blocker: [Brief description]
Task: [Task ID]
Owner: [Specialist/User]
Status: [Open/Resolved]
Next Action: [What needs to happen]
```

## Session End Protocol
- List completed work with commit hashes (real or placeholder if pending).
- Document open blockers with owners and current status.
- Identify the next 3 priority dispatches and their owners.
- Note any spec/reality mismatches discovered during this session.
- Update this cheat sheet with new learnings or refined actions so the guide stays current.

## Today’s Session Example
- Today’s rewrite followed a sequential flow: read `AGENTS.md` → review mode instructions → plan via `update_plan` → replace cheat sheet. This kept focus on documenting every decision.
- Example dispatch split: catching mode-file detours, then crafting the new guide, illustrates the Small-Chunk Principle and how to log blockers when a specialist needs clarification mid-flow.
