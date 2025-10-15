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
