Coder, extract the run state/session restoration logic from `frontend/src/routes/+page.svelte` into a dedicated store under `frontend/src/lib/systems/`.

## Context
- `+page.svelte` declares and mutates core run fields (IDs, map snapshot, battle flags, cached snapshots) inline, making it hard to reason about lifecycle transitions.【F:frontend/src/routes/+page.svelte†L33-L62】【F:frontend/src/routes/+page.svelte†L169-L205】
- The component also owns the persistence helpers (`loadRunState`, `saveRunState`, `clearRunState`) and player config wiring, so any change to run bootstrapping forces edits to the 1.5k-line page file.【F:frontend/src/routes/+page.svelte†L110-L188】

## Requirements
- Build a typed Svelte store (or store family) in `frontend/src/lib/systems/` that encapsulates run identity, party metadata, room snapshot, and battle activity, including the existing persistence helpers.
- Ensure the store exposes explicit async loaders for restoring from storage, syncing player configs, and reacting to backend-provided UI state payloads (currently implemented inside `pollUIState`).【F:frontend/src/routes/+page.svelte†L1392-L1477】
- Update `+page.svelte` to consume the new store(s) so the component only subscribes to state and triggers mutations via clear public methods.
- Provide Vitest unit coverage for the store that exercises: restoring saved runs, merging backend UI state data, and clearing state when runs end.
- Document any state shape changes or new helpers in `frontend/.codex/implementation/run-helpers.md` (append/extend the existing notes file).

## Notes
- Coordinate with the polling and overlay tasks when touching shared globals; surface any remaining inline state that should be migrated in follow-ups.
