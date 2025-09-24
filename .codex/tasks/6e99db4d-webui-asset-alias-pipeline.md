Coder, introduce a metadata-driven alias map for the asset loader.

## Context
- `frontend/src/lib/systems/assetLoader.js` special-cases aliases like `lady_echo → echo` and mimic handling inline, with no way to accept backend-provided alias lists.【F:frontend/src/lib/systems/assetLoader.js†L232-L308】

## Requirements
- Define an alias/asset descriptor shape returned by the backend UI bootstrap (or a new endpoint) that lists ids, alias arrays, asset folders, and mimic rules.
- Update the asset loader to consume the descriptor instead of relying on hard-coded switches, while keeping mimic behavior by deriving the base image id from the metadata.
- Ensure the loader gracefully handles missing aliases and falls back to sane defaults, covering the behavior with unit tests.
- Document the descriptor contract and loader flow in `frontend/.codex/implementation/asset-loading.md`.
- Add acceptance notes to your PR describing the QA checklist for alias handling (e.g., canonical id, alias swap, mimic fallbac
  k) so testers can confirm the metadata-driven loader behavior.

## Notes
- Coordinate with backend developers to expose the descriptor; capture any schema migrations required for the metadata source of truth.
