Coder, establish the central asset registry for character portraits, summons, and backgrounds.

## Context
- `frontend/src/lib/systems/assetLoader.js` mixes portrait logic with summon art (lightstream swords, jellyfish) and background rotations, each maintaining their own normalization helpers.

## Requirements
- Create a shared `assetRegistry` module under `frontend/src/lib/systems/` that exposes typed loaders for character portraits, fallbacks, summon art, and backgrounds.
- Relocate summon art into a dedicated `summons/` folder so it no longer shares directories with character portraits, updating imports accordingly.
- Consolidate URL normalization and caching logic within the new registry module and remove the duplicated helpers from the legacy asset loader.
- Provide unit tests for the registry functions (portrait lookup, fallback cascade, summon asset resolution).
- Document the new registry structure and folder layout in `frontend/.codex/implementation/asset-loading.md`.
- Expose injection points so the registry can accept metadata-provided overrides (alias descriptors, rarity folders, summon alt
  ernative art) as soon as those payloads land, and add tests covering the injected metadata path.

## Notes
- Coordinate with the alias pipeline task to ensure the registry can accept metadata-driven alias descriptors once they land.
