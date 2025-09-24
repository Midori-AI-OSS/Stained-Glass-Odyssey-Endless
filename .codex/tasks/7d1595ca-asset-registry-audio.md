Coder, standardize music and sound effect loading through the asset registry.

## Context
- `frontend/src/lib/systems/music.js` and `frontend/src/lib/systems/sfx.js` expose separate loading conventions, making it difficult to share configuration with the rest of the asset pipeline.

## Requirements
- Move music playlist and sound effect discovery into the central `assetRegistry`, providing typed helpers (`getMusicPlaylist`, `getSfxClip`, etc.).
- Ensure the registry honors reduced-motion and accessibility preferences when selecting default playlists or sound cues.
- Update `music.js` and `sfx.js` to delegate to the registry, deleting duplicated normalization/caching logic.
- Add tests that exercise playlist selection, fallback clips, and reduced-motion behavior.
- Document the new audio registry APIs in `frontend/.codex/implementation/asset-loading.md` or a dedicated audio doc.

## Notes
- Coordinate with the music weighting task to keep metadata formats consistent across character and playlist selection.
