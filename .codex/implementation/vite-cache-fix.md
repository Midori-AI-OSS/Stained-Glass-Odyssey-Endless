# Vite Cache Fix for Navigation Issues

## Issue
The web UI experienced critical navigation and overlay system failures caused by a missing Vite dependency chunk file (`chunk-I6GWL3TI.js`). This resulted in:
- Navigation buttons highlighting but not opening overlays
- 404 errors for dynamically imported modules
- External link buttons not working
- Complete loss of game functionality

## Root Cause
Vite's dependency pre-bundling created an incomplete or corrupted chunk reference in the cache. This prevented the dynamic import system from loading overlay components.

## Solution
Clear the Vite cache directory and restart the development server:

```bash
cd frontend
rm -rf node_modules/.vite
bun run dev
```

## Verification
After clearing the cache and restarting:
1. All navigation buttons (Run, Warp, Inventory, Battle Review, Guidebook, Settings) open their respective overlays
2. External link buttons (Feedback, Discord, Website) properly open new browser tabs
3. No 404 errors in browser console
4. Daily Login Rewards panel loads correctly

## Prevention
If this issue recurs:
1. Check for Vite configuration changes in `vite.config.js`
2. Verify all dependencies are properly installed with `bun install`
3. Consider adding problematic dependencies to `optimizeDeps.exclude` if they cause bundling issues
4. Restart the dev server after major dependency updates

## Related Files
- `frontend/vite.config.js` - Vite configuration
- `frontend/src/lib/systems/OverlayController.js` - Overlay state management
- `frontend/src/lib/components/OverlayHost.svelte` - Overlay rendering component

## Audit Reference
- Audit ID: 6e6becae
- Audit File: `.codex/audit/6e6becae-playwright-webui-audit.md`
- Issues Addressed: #1 (Vite dependency 404), #3 (Overlay system), #4 (External links)
