# Settings Menu

The settings overlay uses a tabbed layout with icon-only buttons for
each category:

- **Audio**: `Volume2` icon.
- **System**: `Cog` icon.
- **LLM**: `Brain` icon, shown only when language model controls are
  available.
- **Gameplay**: `Gamepad` icon.

Each tab's content lives in its own component:

- `AudioSettings.svelte`
- `SystemSettings.svelte`
- `LLMSettings.svelte`
- `GameplaySettings.svelte`

These components share grid and tooltip styling via
`settings-shared.css`, while `SettingsMenu.svelte` handles tab
selection, LRM configuration, and dispatches `save` and `endRun`
events. `SettingsMenu.svelte` receives `backendFlavor` from the page and
checks it for `"llm"` to decide whether the LLM tab should appear. When
the flavor string omits `"llm"`, the component skips `getLrmConfig()`
and hides the model selector and test button.

The Gameplay tab's **End Run** button now attempts to end the current run by
ID and falls back to clearing all runs when the ID is missing or the targeted
request fails.
