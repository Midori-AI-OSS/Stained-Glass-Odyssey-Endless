Coder, source battle music weighting from backend metadata instead of hard-coding the `luna` triple weight.

## Context
- `frontend/src/lib/systems/viewportState.js` boosts `luna` by a factor of three when picking music, ignoring the backend metadata contract described in the implementation docs.【F:frontend/src/lib/systems/viewportState.js†L118-L135】

## Requirements
- Extend the UI bootstrap or roster metadata response to include music weighting information (per character, per encounter, or per playlist) so the frontend no longer hard-codes special cases.
- Update the viewport state/music selection helpers to consume the metadata, gracefully falling back when weights are missing, and remove the inline `id === 'luna' ? 3 : 1` logic.
- Add unit coverage for the weighting selector to verify default behavior, metadata overrides, and reduced-motion fallbacks.
- Document the new metadata fields and weighting rules in `frontend/.codex/implementation/battle-effects.md` (or the relevant audio doc).
- Include acceptance notes in the PR description detailing how QA can verify metadata overrides (e.g., default weight, boosted
  character, and reduced-motion fallback cases) now that the hard-coded multiplier is gone.

## Notes
- Coordinate with backend owners to surface the necessary metadata and document any temporary stubs if the API changes require multiple phases.
