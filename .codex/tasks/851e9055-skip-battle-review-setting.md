Coder, add a gameplay setting that lets players skip the Battle Review overlay.

## Context
- `SettingsMenu.svelte` persists gameplay preferences (reduced motion, animation speed, idle mode) via `saveSettings` but offers no option to bypass the post-fight Battle Review.【F:frontend/src/lib/components/SettingsMenu.svelte†L154-L185】
- The Gameplay tab renders toggles for action values and full idle mode, making it the natural home for a "Skip Battle Review" control.【F:frontend/src/lib/components/GameplaySettings.svelte†L92-L145】
- `OverlayHost.svelte` always opens the Battle Review popup when `reviewOpen && reviewReady`, forcing players through the screen even if they just want to advance.【F:frontend/src/lib/components/OverlayHost.svelte†L372-L398】
- Settings persistence lives in `frontend/src/lib/systems/settingsStorage.js`, so the new toggle must round-trip through local storage and initialization the same way as other gameplay options.【F:frontend/src/lib/systems/settingsStorage.js†L1-L44】

## Requirements
- Add a `skipBattleReview` boolean to the settings schema, including load/save logic, defaulting to `false` for existing players.
- Surface a checkbox (or similar control) within the Gameplay settings tab that flips `skipBattleReview`, reusing the tooltip/label styling and wiring it into the existing debounced `scheduleSave` flow.
- Teach `OverlayHost` (and any other review gating logic) to respect the flag: when enabled, immediately dispatch the `nextRoom` progression after logging battle results without mounting the Battle Review overlay.
- Ensure the skip path still honors reward handling—only bypass the review when there are no outstanding loot choices and the backend has marked the battle complete.
- Update initialization code (`viewportState`, overlay stores) so the skip flag is available when deciding whether to request summaries or prefetched data.
- Provide tests to cover settings persistence and overlay branching (e.g., Vitest components or store unit tests that confirm review bypass behavior).
- Document the new toggle in `frontend/.codex/implementation/settings-menu.md` and cross-link from the Battle Review documentation so players know how to disable the timeline screen once the redesign ships.

## Notes
- Coordinate with the timeline overhaul (task d6ec9364) so skip behavior gracefully handles future review modules.
- Consider analytics or logging hooks to measure how often players skip the review for future UX tuning.

Task ready for implementation.

## Implementation Complete ✅

**Status**: Complete  
**Implementation Date**: September 21, 2025  
**Implemented by**: @copilot

### Summary
Successfully implemented the Skip Battle Review gameplay setting. Players can now bypass the Battle Review overlay and advance directly to the next room after battle completion by enabling the toggle in Gameplay settings.

### Changes Made
- ✅ Added `skipBattleReview` boolean setting to settings storage with proper persistence
- ✅ Created UI checkbox control in GameplaySettings with SkipForward icon and tooltip
- ✅ Modified OverlayHost logic to respect skip flag and auto-advance when enabled
- ✅ Ensured proper data flow through component hierarchy
- ✅ Added comprehensive tests for settings persistence and overlay behavior
- ✅ Updated documentation with cross-references between settings and battle review docs

### Files Modified
- `frontend/src/lib/systems/settingsStorage.js` - Settings storage logic
- `frontend/src/lib/systems/viewportState.js` - Settings initialization  
- `frontend/src/lib/components/SettingsMenu.svelte` - Settings menu integration
- `frontend/src/lib/components/GameplaySettings.svelte` - UI control
- `frontend/src/lib/components/OverlayHost.svelte` - Skip logic implementation
- `frontend/src/lib/components/GameViewport.svelte` - Data flow
- `frontend/tests/skip-battle-review-setting.test.js` - Test coverage
- `frontend/.codex/implementation/settings-menu.md` - Documentation
- `frontend/.codex/implementation/battle-review-ui.md` - Documentation

### Validation
- ✅ Manual testing confirms setting persistence and UI functionality
- ✅ All tests pass including new comprehensive test suite
- ✅ Follows existing code patterns and minimal-change principle
- ✅ Coordinates with future timeline overhaul (task d6ec9364)
