Coder, remove per-character hard-coding from the WebUI and source data from backend metadata.

## Context
- `frontend/src/routes/+page.svelte` seeds the party with `['sample_player']`, a placeholder id that leaks into run creation until the player reselects a roster.【F:frontend/src/routes/+page.svelte†L30-L39】
- `frontend/src/lib/systems/viewportState.js` gives the character id `luna` triple weight when picking battle music, rather than reading any weighting from backend data.【F:frontend/src/lib/systems/viewportState.js†L118-L135】
- `frontend/src/lib/systems/assetLoader.js` includes hard-coded aliases such as `lady_echo → echo` and special-cases mimic behavior, with no way for backend-driven alias lists to flow in.【F:frontend/src/lib/systems/assetLoader.js†L232-L308】
- The current documentation in `frontend/.codex/implementation/party-ui.md` and `frontend/.codex/implementation/battle-effects.md` assumes the UI reflects backend metadata, but the hard-coded values above break that contract.

## Requirements
- Replace the `'sample_player'` default with a dynamic roster-derived seed (e.g., automatically select the first available player id after fetching `getPlayers()`), and ensure party state stays empty until real data arrives.
- Update the music selection logic to consume weighting metadata from backend responses or a configuration map returned by `getPlayers()`/`getUIState()`, falling back gracefully when weights are missing. Remove the inline `id === 'luna' ? 3 : 1` logic.
- Expose a structured alias map (e.g., `{ id, aliases, assetFolder }`) from the backend UI bootstrap or a new endpoint, and update the asset loader to honor it instead of shipping hard-coded switches. Keep mimic behavior but derive the base image id from metadata where possible.
- Audit the WebUI for any other name-based conditionals (e.g., summons, overlays, UI badges) and replace them with metadata-driven flags supplied by the backend. Document any new keys expected from API responses.
- Update relevant `.codex/implementation` docs (party UI, battle viewer, asset loading) to describe the new metadata fields and remove references to the deleted hard codes.

## Notes
- Coordinate with backend developers if additional metadata must be added to existing endpoints; include acceptance notes in the task PR so QA knows what to verify.
- Ensure existing players retain their saved parties after the migration—perform necessary state migrations or validation when loading persisted run data.

Task ready for implementation.
