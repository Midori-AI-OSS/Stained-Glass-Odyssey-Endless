# Settings Menu

`SettingsMenu.svelte` now follows the options spec. It includes Lucide icons,
labels, and tooltips for **SFX Volume**, **Music Volume**, **Voice Volume**,
**Framerate**, and an **Autocraft** toggle. Controls are grouped under
**Audio**, **UI**, **System**, and **Gameplay** headings, with the optional
**LLM** tab appearing when a language-model backend is detected.

`UISettings.svelte` contains all theme and motion controls, including palette
selection, static/custom background pickers, custom accent color selection,
and granular motion toggles. These controls call `updateThemeSettings` and
`updateMotionSettings` so the shared stores update immediately while the
debounced `scheduleSave()` keeps legacy options in sync.

The selected framerate is saved as a number and merged with existing settings in local storage so server polling limits persist across sessions.
`frameratePersistence.test.js` verifies the viewport loads this saved value on startup.

Settings auto-save when sliders, checkboxes, or selects change. A debounced `save()` helper persists the latest values via `saveSettings` and briefly displays a "Saved" indicator.

Choosing **Wipe Save Data** prompts for confirmation. If accepted, the app calls the `/save/wipe` endpoint with error handling.
On success it deletes runs, options, and damage type records from the backend database, clears stored settings, resets menu values
to defaults, and displays a status message confirming the wipe. Errors surface a failure message.

## Testing
- `bun test`
- `pytest`
