Coder, finish the root page refactor by updating documentation and adding regression coverage.

## Context
- Breaking `frontend/src/routes/+page.svelte` into stores and utilities needs corresponding documentation and QA updates so future contributors understand the new module boundaries.【F:frontend/src/routes/+page.svelte†L1-L80】
- Existing docs in `frontend/.codex/implementation/battle-review-ui.md` and related notes still describe the monolithic page and the legacy helper flags.

## Requirements
- After the new stores/utilities land, sweep the frontend `.codex/implementation` docs (battle review, party UI, viewport state) and update them to reference the extracted modules and the removal of inline helpers.
- Add regression coverage for the root page integration points: e2e or component tests that verify overlays launch, run polling transitions correctly, and the viewport initializes without the legacy globals.
- Coordinate with QA to capture a test checklist for the new module boundaries and commit it to `.codex/instructions/` or the relevant service docs.
- Ensure the new tests are wired into the existing frontend test runner and documented in the developer guide so contributors know how to execute them locally.

## Notes
- This task depends on the modularization task landing first; document any follow-up tickets if further cleanup is required.
