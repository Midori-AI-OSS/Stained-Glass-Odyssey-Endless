Coder, audit the WebUI for other name-based conditionals and replace them with metadata-driven flags.

## Context
- Several UI flows (summons, overlays, UI badges) still branch on character ids directly, undermining the backend-driven metadata story described in the implementation docs.

## Requirements
- Sweep the frontend codebase for hard-coded character ids or names that change behavior (summon overrides, overlay badges, event gating) and catalogue them.
- For each conditional, extend the backend metadata (UI bootstrap or specific endpoints) to expose explicit flags/attributes, then update the frontend to consume them instead of comparing ids.
- Ensure the new metadata is documented in the relevant `.codex/implementation` files and add regression tests where practical to prevent new hard-coded branches from creeping back.
- Provide a migration/testing checklist summarizing the replacements and commit it alongside the code changes.
- Include acceptance notes in the PR description that outline the QA validation steps for each replaced conditional so the revi
  ew team can confirm metadata flags drive the new behaviors.

## Notes
- Coordinate with the alias pipeline and music weighting tasks so shared metadata structures stay consistent across features.
