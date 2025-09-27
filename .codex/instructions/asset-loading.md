# Asset Loading

All runtime asset resolution now flows through the central registry in
`frontend/src/lib/systems/assetRegistry.js`. The registry eagerly snapshots
Vite's `import.meta.glob` results and exposes helper APIs for portraits,
summons, music, materials, DoT icons, and status-effect glyphs. Callers must
use the exported helpers (`getCharacterImage`, `getSummonArt`,
`getRewardArt`, `getDotImage`, `getEffectImage`, etc.) instead of touching
`import.meta.glob` directly.

- **Portraits & Summons**: `registerAssetManifest` loads canonical ids while
  `registerAssetMetadata` supports alias tables, mirror rules, background
  overrides, and summon portrait galleries. Fallback selections emit a
  `portrait-fallback` or `summon-fallback` telemetry event when no on-disk
  art is available.
- **Rewards & Materials**: `getRewardArt` and `getMaterialIcon` automatically
  dedupe ids and fall back to deterministic placeholders. Metadata can
  inject overrides via
  `registerAssetMetadata({ rewardOverrides: { item: { key: { url, metadata } } } })`.
  Override metadata is retrievable with `getRewardMetadata(type, id)`.
- **Audio**: The registry builds playlists from `assets/music` and exposes
  `getMusicPlaylist`, `getMusicFallbackPlaylist`, and
  `getRandomMusicTrack`. Metadata payloads can extend or replace tracks with
  the following shape:

  ```js
  registerAssetMetadata({
    musicOverrides: {
      becca: {
        defaultCategory: 'boss',
        tracks: {
          boss: [
            { url: 'https://example.com/theme.mp3', metadata: { composer: 'QA' } }
          ]
        }
      }
    },
    musicFallbacks: {
      normal: [
        { url: 'https://example.com/fallback.mp3', metadata: { composer: 'Fallback Team' } }
      ]
    },
    musicAnnotations: {
      'https://example.com/theme.mp3': { mood: 'intense' }
    }
  });
  ```

  Track metadata can be queried with `getMusicTrackMetadata(url)`.
- **DoT & Effect Icons**: `assetLoader.js` now delegates element pools and
  glyph lookups to the registry via `getDotVariantPool`, `getDotFallback`,
  `getEffectIconUrl`, and `getEffectFallback`. This keeps the loader free of
  direct glob usage while preserving the deterministic hashing rules.

## Telemetry & QA Troubleshooting

Registry failures emit structured telemetry. Use
`setAssetRegistryTelemetry(handler)` in tests or debug builds to receive
events in-process, or listen for the browser event
`autofighter:asset-registry`:

```js
import { setAssetRegistryTelemetry } from '$lib/systems/assetRegistry';

setAssetRegistryTelemetry(event => {
  console.log('asset registry', event.kind, event.detail);
});

// In the browser, QA can run:
window.addEventListener('autofighter:asset-registry', ({ detail }) => {
  console.warn('Asset registry fallback', detail.kind, detail.detail);
});
```

Each telemetry payload includes a `kind`, human-readable `reason`, and the id
or key that failed to resolve. QA troubleshooting steps:

1. Reproduce the missing asset and confirm a telemetry event fired.
2. Inspect the `reason` field (`player-pool`, `mirror-static`,
   `missing-icon`, `empty-gallery`, etc.) to identify whether metadata or
   on-disk assets are missing.
3. Cross-check any `metadata` payload returned by `getRewardMetadata` or
   `getMusicTrackMetadata` to ensure backend descriptors were applied.

Remember to call `resetAssetRegistryOverrides()` (or restart the app) before
retesting so the telemetry cache clears between runs.
