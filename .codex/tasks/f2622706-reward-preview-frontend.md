# Render staged reward previews in the frontend overlay

## Summary
Consume the backend preview metadata and surface it in `RewardOverlay` with readable stat deltas and trigger descriptions.

## Requirements
- Update the UI API layer (`frontend/src/lib/systems/uiApi.js` or equivalent) and related stores to read the new preview payload from reward responses and battle snapshots.
- Extend `RewardOverlay.svelte` (and any child components) to present staged stat changes, trigger counts, or other preview signals without regressing the existing reward list layout.
- Provide helper mappers that translate backend schema fields into localized text/numeric displays; ensure they degrade gracefully when previews are missing.
- Add Storybook examples or screenshot references demonstrating at least one card and one relic preview.
- Document the UI contract in `.codex/implementation/reward-overlay.md` so designers know which elements are now required.

## Dependencies
Complete the backend preview schema task (`b30ad6a1-reward-preview-schema.md`) first.

## Out of scope
Guardrails, staging confirmation logic, and backend tests belong to other tasks.

## Auditor summary (2025-02-19)
- Frontend normalises staged reward previews and renders stat/trigger panels for cards and relics, and the UI API integrates the `reward_staging.preview` payloads.【F:frontend/src/routes/+page.svelte†L972-L1056】【F:frontend/src/lib/components/RewardOverlay.svelte†L1-L340】
- `RewardPreviewFormatter` covers summary/stat formatting and has Vitest coverage, but the documentation references screenshot files (`reward-overlay-card-preview.png`, `reward-overlay-relic-preview.png`) that are not present under `.codex/screenshots/`, so designers cannot review the new layout assets.【F:.codex/implementation/reward-overlay.md†L12-L25】【bccb0e†L1-L1】
- `tests/battlepolling.test.js` still expects `if (snap?.error)` inside `+page.svelte`, and the string is absent, causing `bun test tests/battlepolling.test.js` to fail (the test inspects the file contents).【F:frontend/tests/battlepolling.test.js†L8-L33】【F:frontend/src/routes/+page.svelte†L1-L120】【4f5838†L1-L1】

more work needed
