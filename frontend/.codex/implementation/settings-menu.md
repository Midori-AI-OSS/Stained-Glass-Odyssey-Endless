# Settings Menu

The settings overlay uses a tabbed layout with icon-only buttons for each category:

- **Audio**: `Volume2` icon.
- **System**: `Cog` icon.
- **LLM**: `Brain` icon, shown only when language model controls are available.
- **Gameplay**: `Gamepad` icon.

Each tab's content lives in its own component:

- `AudioSettings.svelte`
- `SystemSettings.svelte`
- `LLMSettings.svelte`
- `GameplaySettings.svelte`

All tabs share a two-column grid defined in `settings-shared.css`. Labels and Lucide icons occupy the left column while interactive controls sit on the right, and rows fade on hover. The stylesheet also provides tooltip styling consumed by `Tooltip.svelte`.

The tab selector bar reuses the navigation bar’s stained-glass styling via the `stained-glass-bar` class so the tabs visually match other glass elements.

Audio volume controls use the `DotSelector` component to render ten selectable levels (0–100%). Gameplay controls that need explanations wrap their labels in the `Tooltip` component for accessible hover and focus hints. System settings include icons for backend health (`activity`), framerate (`gauge`), reduced motion (`move`), wipe (`trash-2`), backup (`download`), and import (`upload`).

`SettingsMenu.svelte` handles tab selection, LRM configuration, and dispatches `save` and `endRun` events. `SettingsMenu.svelte` receives `backendFlavor` from the page and checks it for `"llm"` to decide whether the LLM tab should appear. When the flavor string omits `"llm"`, the component skips `getLrmConfig()` and hides the model selector and test button.

The Gameplay tab's **End Run** button now attempts to end the current run by ID and falls back to clearing all runs when the ID is missing or the targeted request fails.

The Gameplay tab also exposes an **Animation Speed** slider (0.1–2.0×). Adjusting it writes the selected multiplier to settings storage and posts the derived turn pacing (`base_turn_pacing / animationSpeed`) to `/config/turn_pacing` so backend battle pacing matches the UI setting.
