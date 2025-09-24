Coder, migrate card, relic, and material asset loading into the central registry.

## Context
- `frontend/src/lib/systems/rewardLoader.js` and `frontend/src/lib/systems/materialAssetLoader.js` repeat `import.meta.glob` patterns and normalization helpers already needed by the base asset registry.

## Requirements
- Extend the `assetRegistry` to expose loaders for cards, relics, and inventory materials (icons + glyphs) using shared caching and normalization logic.
- Delete the redundant helpers from `rewardLoader.js` and `materialAssetLoader.js`, updating all call sites to consume the registry instead.
- Ensure Vite's static `import.meta.glob` analysis remains valid by declaring globs at module scope in the registry.
- Add regression tests for the reward/material loaders to confirm cache hits, fallback behavior, and glyph pairing.
- Update `frontend/.codex/implementation/asset-loading.md` with the new API surface and migration notes.

## Notes
- Coordinate with design/content teams if folder structures need to change to support the unified registry.
