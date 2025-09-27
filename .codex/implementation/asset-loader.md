# Asset Loader

`assetLoader.js` is now a thin façade over the central asset registry. Rather than
running its own `import.meta.glob` calls, the loader imports the registry helpers
(`getCharacterImage`, `getSummonArt`, `getDotVariantPool`, `getEffectIconUrl`,
etc.) and focuses on presentation logic (color palettes, Lightstream sword
grouping, deterministic hashing). This keeps the bundle free of duplicate glob
work and allows metadata overrides to flow through a single code path.

- Character portraits, backgrounds, DoT icons, and summons are resolved through
  the registry. When galleries are missing, the loader receives the registry's
  normalized fallback URL and the telemetry system records a
  `portrait-fallback` or `summon-fallback` event for QA.
- Reward art and material icons are delegated to the registry's caches so new
  metadata (e.g. `rewardOverrides`) immediately takes effect. Inventory panels
  call `getMaterialIcon`/`onMaterialIconError` instead of globbing their own
  folders.
- Status-effect sprites pull from `getEffectIconUrl` with type-aware fallbacks.
  When neither metadata nor disk art exists, the registry returns
  `getEffectFallback('buffs' | 'debuffs')`, keeping the loader logic trivial.
- Audio helpers (`getMusicPlaylist`, `getRandomMusicTrack`) now return metadata
  annotated by `registerAssetMetadata` so UI components or QA tooling can check
  composers, BPM, or other injected properties via `getMusicTrackMetadata`.

The module is still shared by the party picker, map display, and battle view so
character images and type colors stay in sync across the UI. Telemetry can be
observed with `setAssetRegistryTelemetry` or the `autofighter:asset-registry`
browser event when debugging missing assets.

## Testing
- `bun test frontend/tests/assetloader.test.js`
- `bun test frontend/tests/asset-registry-runflow.test.js`
