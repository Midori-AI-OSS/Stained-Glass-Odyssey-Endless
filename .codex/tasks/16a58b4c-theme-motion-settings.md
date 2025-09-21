Coder, expand the WebUI settings to support theming and granular motion control.

## Context
- `frontend/src/lib/components/SettingsMenu.svelte` currently exposes Audio/System/Gameplay tabs with a single Reduced Motion toggle and no theme configuration.
- `frontend/src/lib/components/SystemSettings.svelte` only offers a boolean Reduced Motion checkbox and fixed framerate options; there is no way to opt out of specific animations like StarStorm, battle floaters, or portrait glows.
- `frontend/src/lib/components/GameViewport.svelte` hard-codes the accent color to the user's level via `levelToAccent`, so players cannot override the palette or background rotation.
- `frontend/src/lib/systems/settingsStorage.js` persists only simple numeric/boolean settings and lacks schema support for themes or nested accessibility preferences.

## Requirements
- Introduce a theme system that lets players pick from predefined palettes (e.g., "Default", "Solaris", "Nocturne") or supply a custom accent/background. The selection should drive `GameViewport` styling instead of the current level-derived hue.
- Provide controls to choose background behavior (hourly rotation, static pick, custom asset) and whether decorative layers like `StarStorm.svelte` render at all.
- Replace the single Reduced Motion toggle with a tree of options (e.g., "Global Reduced Motion", "Disable Floating Damage Popups", "Disable Portrait Glows", "Simplify Overlay Transitions"). Respect `prefers-reduced-motion` by defaulting the root switch appropriately.
- Persist the new settings structure in `settingsStorage.js` with backward-compatible migration logic so existing players keep their saved volumes/animation speed.
- Ensure all major animation-producing components (`StarStorm.svelte`, `BattleEventFloaters.svelte`, `BattleFighterCard.svelte`, overlay transitions) read the new granular flags and adjust behavior without extra prop plumbing in every call site.
- Update the settings documentation in `frontend/.codex/implementation/settings-menu.md` to describe the theme picker and motion sub-options, including UX expectations.

## Notes
- Consider exposing a preview area in the Settings overlay so players can see their theme choices before closing the dialog.
- Do not regress keyboard navigation: all new controls must be reachable via tab order and have accessible labels.

Task ready for implementation.
