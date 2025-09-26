# Asset Loader

`assetLoader.js` centralizes character portraits, backgrounds, and damage type assets for the frontend.

- Character portraits are loaded from `frontend/src/lib/assets/characters` and resolved to absolute URLs via Vite's `import.meta.glob(..., { as: 'url', eager: true })`. When `import.meta.glob` isn't available (e.g., during tests), the loader returns an empty map and relies on fallback logic. Missing portraits fall back to the repository logo.
- Backgrounds rotate hourly using a seeded random selector and fall back to the repository logo when none are available.
- `getElementIcon` and `getElementColor` expose consistent damage type icons and colors for Fire, Ice, Lightning, Light, Dark, Wind, and Generic types.

The loader lives in `frontend/src/lib/systems/assetLoader.js` and is shared by the party picker, map display, and battle view so character images and type colors stay in sync across the UI. URL handling is normalized so root-relative or absolute URLs are not re-resolved, preventing malformed `file://` URLs in non-browser contexts. Alias rules now arrive via `registerAssetManifest`, allowing the backend to define canonical ids, alternate names (for example `lady_echo → echo`), summon portrait reuse, and mirror targets without baking those maps into the bundle.

## Testing
- `bun test frontend/tests/assetloader.test.js`
