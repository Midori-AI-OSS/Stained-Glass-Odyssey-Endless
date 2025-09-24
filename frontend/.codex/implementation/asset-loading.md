# Asset Loading Registry

## Overview
The frontend consolidates asset discovery in `src/lib/systems/assetRegistry.js`.
The registry normalizes URLs returned by Vite's `import.meta.glob`, caches
random selections, and exposes typed loaders so callers no longer have to know
where portraits, summons, or fallbacks are stored on disk. `assetLoader.js`
re-exports the registry APIs to preserve the existing import surface while still
housing the element icon helpers and damage-type palette utilities.

### Responsibilities
- Normalize all asset URLs via `normalizeAssetUrl`.
- Track portrait galleries, fallback pools, summon galleries, and background
  rotations.
- Provide cache-aware accessors such as `getCharacterImage`,
  `getRandomFallback`, `getSummonArt`, `getSummonGallery`,
  `getHourlyBackground`, and `getRandomBackground`.
- Surface collection helpers including `hasCharacterGallery`,
  `advanceCharacterImage`, `getAvailableCharacterIds`, and
  `getAvailableSummonIds`.
- Expose metadata injection hooks through `registerAssetMetadata` so upcoming
  payloads can override folders, alias descriptors, rarity folders, summon
  variants, or fallback/background URLs at runtime.
- Support test and runtime reset through `resetAssetRegistryOverrides`, which
  clears metadata overrides, invalidates caches, and bumps the registry
  version.

The registry increments an internal `registryVersion` counter whenever metadata
changes. Consumers such as the lightstream sword helper in `assetLoader.js`
rebuild their cached views only when the version changes.

## Directory Structure
```
frontend/src/lib/assets/
├── backgrounds/         # Hourly and random background rotation
├── characters/          # Player and NPC portrait folders
│   └── fallbacks/       # Portrait fallback pool
├── dots/                # Damage-over-time icons grouped by element
├── effects/             # Buff/debuff icons grouped by effect type
└── summons/             # NEW: summon artwork (lightstream swords, jellyfish, etc.)
```

The new `summons/` directory houses lightstream sword art and jellyfish renders
so they no longer mix with character portraits. The registry builds summon
“galleries” using both on-disk art and any injected metadata entries; callers
can inspect galleries with `getSummonGallery` or resolve a single URL with
`getSummonArt` (optionally filtered or seeded).

Portrait aliases such as the Mimic or jellyfish variants are handled inside the
registry so callers continue to request `getCharacterImage('jellyfish_alpha')`
and receive the shared summon art.

## Metadata Injection
`registerAssetMetadata` accepts the following keys (all optional):

- `portraitAliases`: map alias → canonical portrait id.
- `portraitOverrides`: map id → URL or array of URLs (replaces gallery entries).
- `fallbackOverrides`: array of URLs prepended to the fallback pool.
- `backgroundOverrides`: array of URLs appended to the background rotation.
- `summonAliases`: map alias → canonical summon id.
- `summonOverrides`: map id → URL, array of URLs, or objects with
  `{ url, element, metadata }`.
- `rarityFolders`: map portrait id → array of rarity folder descriptors.

Overrides merge with on-disk assets and are available immediately because cache
maps are cleared and the registry version increments. Tests and tooling can
reset overrides with `resetAssetRegistryOverrides()` to restore the on-disk
state.

## Legacy Loader Interaction
`assetLoader.js` now imports the typed loaders from the registry and re-exports
them to maintain backwards compatibility. The module continues to host element
color/icon helpers, DoT/effect icon lookups, and the lightstream sword element
inference logic. The sword helpers call `getSummonGallery('lightstreamswords')`
and only recompute their element-indexed map when the registry version changes.

Downstream code (Svelte components, tests, and utilities) can continue to import
from `assetLoader.js` while benefiting from the centralized registry and the new
summon directory layout.
