Coder, unify the WebUI asset loading pipeline into a single registry.

## Context
- `frontend/src/lib/systems/assetLoader.js` hand-rolls URL normalization and caches for characters, backgrounds, DoT icons, and lightstream swords that currently live alongside character portraits instead of under a summons-specific grouping.
- `frontend/src/lib/systems/rewardLoader.js` and `frontend/src/lib/systems/materialAssetLoader.js` repeat similar `import.meta.glob` + `normalizeUrl` logic for cards, relics, and items.
- `frontend/src/lib/systems/music.js` and `frontend/src/lib/systems/sfx.js` expose separate loading conventions for audio assets, making it hard to standardize how sounds are discovered/configured.
- The asset-loading implementation notes in `frontend/.codex/implementation/asset-loading.md` no longer match the current code, and there is no single surface for coders to plug in future asset families (e.g., UI backgrounds, particle packs).

## Requirements
- Design a central `assetRegistry` (or similar) inside `frontend/src/lib/systems/` that exposes typed loaders for:
  - character portraits, fallbacks, lightstream sword art, jellyfish summons, and background rotations (with swords/jellyfish relocated into a dedicated `summons/` folder so they no longer mix with character art);
  - cards, relics, inventory materials (icons + glyphs);
  - music playlists and sound effects.
- Deduplicate and delete one-off helpers such as the `normalizeUrl` copies in `assetLoader.js` and `rewardLoader.js`, and consolidate caching into the shared registry.
- Provide a consistent API that callers across the app can import (e.g., `getCharacterImage`, `listBackgrounds`, `getMusicPlaylist`, `getSfxClip`), replacing the bespoke exports in the existing modules.
- Ensure the registry supports injecting metadata (aliases, rarity folders, etc.) instead of hard-coded heuristics, preparing the codebase for backend-provided asset descriptors.
- Update all call sites to use the new registry while maintaining existing functionality (portraits should still randomize per session, rewards still resolve art, music still honors battle context, etc.).
- Refresh `frontend/.codex/implementation/asset-loading.md` so the documentation matches the unified pipeline and describes how new asset families should be registered.

## Notes
- Be careful to keep Vite's static `import.meta.glob` analysis working—registry helpers still need to declare the globs at module scope.
- Provide unit coverage or integration tests for the registry functions where practical (especially alias resolution and fallback ordering).

Task ready for implementation.
