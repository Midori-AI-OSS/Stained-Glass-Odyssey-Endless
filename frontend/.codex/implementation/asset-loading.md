# Asset Loading Registry

## Overview
The frontend consolidates asset discovery in `src/lib/systems/assetRegistry.js`.
The registry normalizes URLs returned by Vite's `import.meta.glob`, caches
random selections, and exposes typed loaders so callers no longer have to know
where portraits, summons, or fallbacks are stored on disk. `assetLoader.js`
re-exports the registry APIs to preserve the existing import surface while still
housing the element icon helpers and damage-type palette utilities.

### Backend-driven manifest
`GET /ui` now includes an `asset_manifest` payload that the frontend passes to
`registerAssetManifest` before rendering any portrait-bound components. The
descriptor lists canonical ids, alias arrays, the relative asset folder, and an
optional `mimic` object for entries that mirror another gallery. Summons can set
`portrait: true` to expose their gallery through the portrait helpers.

Example snippet:

```json
{
  "portraits": [
    {
      "id": "echo",
      "folder": "characters/echo",
      "aliases": ["lady_echo"]
    },
    {
      "id": "mimic",
      "folder": null,
      "aliases": [],
      "mimic": { "mode": "player_mirror", "target": "player" }
    }
  ],
  "summons": [
    {
      "id": "jellyfish",
      "folder": "summons/jellyfish",
      "aliases": [
        "jellyfish_healing",
        "jellyfish_electric",
        "jellyfish_poison",
        "jellyfish_shielding"
      ],
      "portrait": true
    }
  ]
}
```

The registry normalises this descriptor, caches a digest to avoid redundant
cache invalidation, and exposes mirror rules to the mimic resolver so
`portrait_pool: player_mirror` derives its base id from metadata rather than a
hard-coded `player` check. Passing `null` clears the manifest and exercises the
fallback behaviour in tests.

### Responsibilities
- Normalize all asset URLs via `normalizeAssetUrl`.
- Track portrait galleries, fallback pools, summon galleries, and background
  rotations.
- Provide cache-aware accessors such as `getCharacterImage`,
  `getRandomFallback`, `getSummonArt`, `getSummonGallery`,
  `getHourlyBackground`, and `getRandomBackground`.
- Surface card, relic, and material reward loaders via `getRewardArt`,
  `getGlyphArt`, and `getMaterialIcon` so Svelte components share caching and
  fallback logic.
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

## Reward and Material Assets
`assetRegistry.js` now owns the reward loaders that used to live in
`rewardLoader.js` and `materialAssetLoader.js`.

- `getRewardArt(type, id)` indexes card, relic, and item artwork using Vite's
  static module maps. The helper normalizes ids (folder/id for cards and
  relics, compact ids for items), caches lookups, and falls back to
  `getMaterialFallbackIcon()` for unknown entries.
- `getGlyphArt(type, entry)` performs the glyph pairing used by card/relic
  frames. It compacts the entry id and name to locate drop-in glyph art and
  returns an empty string when no match exists.
- `getMaterialIcon(key)` returns the best inventory material icon based on the
  `<element>_<rank>` key. The loader prefers element/rank specific art, then
  generic assets for the requested rank, and finally the shared fallback icon.
  `getMaterialFallbackIcon()` exposes the generic fallback URL, while
  `onMaterialIconError(event)` applies it when an `<img>` fails to load.

## Audio Assets

Audio discovery now lives inside the registry so background music and SFX share
normalisation, caching, and accessibility guards.

- `getMusicPlaylist(characterId, category, options?)` resolves a playlist for a
  combatant. Categories are inferred from the on-disk folder structure (`normal`,
  `weak`, `boss`, etc.). Passing `{ reducedMotion: true }` or `{ muted: true }`
  returns an empty list so the caller can skip playback entirely.
- `getMusicFallbackPlaylist(category, options?)` and
  `getAllMusicTracks(options?)` expose the shared soundtrack library and obey the
  same accessibility flags.
- `getRandomMusicTrack(characterId, category, options?)` mirrors the previous
  helper while respecting registry preferences and returning `''` when audio is
  muted.
- `getSfxClip(key, options?)` resolves UI sound cues via canonical ids or
  friendly aliases such as `ui/pull/deal`. Options support `{ fallback: true }`
  to return the default UI clip when a key is missing, and `{ reducedMotion: true }`
  to silence the response.
- `getAvailableSfxKeys()` returns a deduplicated list of canonical clip ids and
  aliases so tooling can validate configuration.

`createDealSfx` now calls `getSfxClip('ui/pull/deal')` and forwards the overlay's
reduced-motion flag, preventing the dealing animation from triggering audio for
players who opt out of motion effects.

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

### Character metadata hooks

`getCharacterImage` now consults the lightweight registry in
`src/lib/systems/characterMetadata.js` before resolving portraits. The registry
is populated from backend responses (e.g. `/players`) so components can register
additional hints without duplicating conditionals. The following metadata keys
are respected:

- `portrait_pool`: `player_mirror` mirrors the main player's gallery (used by
  Mimic) while `player_gallery` forces the random player fallback without
  special-casing ids such as `lady_echo`.
- `non_selectable`: hides characters from the party picker regardless of
  `gacha_rarity`.

Callers can pass `{ metadata }` via the second argument to `getCharacterImage`
for one-off lookups, but typical flows populate the shared registry with
`replaceCharacterMetadata()` so roster data, summons, and pull results all share
the same hints.

## Legacy Loader Interaction
`assetLoader.js` now imports the typed loaders from the registry and re-exports
them to maintain backwards compatibility. The module continues to host element
color/icon helpers, DoT/effect icon lookups, and the lightstream sword element
inference logic. The sword helpers call `getSummonGallery('lightstreamswords')`
and only recompute their element-indexed map when the registry version changes.

Downstream code (Svelte components, tests, and utilities) can continue to import
from `assetLoader.js` while benefiting from the centralized registry and the new
summon directory layout.
