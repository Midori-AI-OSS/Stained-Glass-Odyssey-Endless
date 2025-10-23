# Refresh reward overlay documentation set

## Summary
Update documentation artifacts so they describe the four-phase reward flow, new confirm interactions, and automation touchpoints introduced by the overhaul.

## Requirements
- Revise `frontend/.codex/implementation/reward-overlay.md` with the new phase diagram, countdown behaviour, confirm interactions, and fallback notes.
- Document the state machine API for other contributors (inputs, events, hooks) and link to any shared styling token sources.
- Audit other docs (automation guides, QA notes, README excerpts) referencing the old single-phase overlay and update them or flag obsolete references.
- Include callouts for accessibility expectations (focus order, screen reader announcements) so reviewers know what to validate.
- Coordinate with QA/automation owners to capture any new manual testing steps introduced by the countdown or confirm flows.

## Coordination notes
- Share the updated docs with coders once the major UI tasks land to confirm accuracy.
- If documentation gaps remain after UI/testing work completes, outline follow-up tasks in this file.
ready for review
