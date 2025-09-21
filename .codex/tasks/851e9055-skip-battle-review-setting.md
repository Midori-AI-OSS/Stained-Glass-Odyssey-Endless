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
