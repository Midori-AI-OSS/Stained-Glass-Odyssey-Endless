# Document reward preview authoring guidelines

## Summary
Capture examples and authoring guidance so plugin developers know how to populate preview metadata for cards and relics once the backend and frontend support exists.

## Requirements
- Produce documentation updates in `.codex/implementation/reward-overlay.md` and `.codex/implementation/battle-endpoint-payload.md` that walk through how preview fields are generated and consumed.
- Add at least three worked examples covering a flat stat buff, a conditional trigger, and a passive-style subscription, including which plugin hooks should emit preview data.
- Update any contributor docs in `.codex/instructions/` that explain reward implementation so they reference the new preview workflow.
- Coordinate with the Task Master board to link this doc task to `b30ad6a1-reward-preview-schema.md` and `f2622706-reward-preview-frontend.md` so coders know when to schedule it.

## Dependencies
Complete backend and frontend preview tasks first to ensure documentation matches implemented behavior.

## Out of scope
No code or UI changes—this task is documentation-only.
