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

The tab selector bar reuses the navigation bar's stained-glass styling via the `stained-glass-bar` class so the tabs visually match other glass elements.

## System Settings

The System settings tab is organized into several sections:

### Theme Settings
- **Theme Palette**: Dropdown selector with predefined themes:
  - `Default`: Uses level-based hue progression (original behavior)
  - `Solaris`: Warm orange theme (#ffb347)
  - `Nocturne`: Purple theme (#9370db)
  - `Custom`: Allows user-defined accent color via color picker
- **Custom Accent**: Color picker (shown only when Custom theme selected)
- **Background Mode**: Controls background behavior:
  - `Hourly Rotation`: Changes background assets every hour
  - `Static Pick`: Uses a fixed background from predefined options
  - `Custom Asset`: Allows custom background upload via file picker
- **Static Background**: Dropdown selector with predefined background images (shown only when Static Pick selected)
- **Custom Background**: File picker for uploading custom background images (shown only when Custom Asset selected)

The selected theme drives `GameViewport` styling instead of the level-derived hue system, providing consistent visual themes independent of player progression.

### Motion & Accessibility Settings
Replaces the single "Reduced Motion" toggle with granular accessibility controls:

- **Global Reduced Motion**: Master switch that respects `prefers-reduced-motion` system preference
- **Disable Floating Damage**: Turns off `BattleEventFloaters` damage popups and battle text
- **Disable Portrait Glows**: Removes glowing effects from `BattleFighterCard` portraits
- **Simplify Overlay Transitions**: Uses simpler transitions for overlays and menus
- **Disable Star Storm**: Turns off the animated `StarStorm.svelte` background effect
- **Enable RPG Maker FX**: Opt-in switch for Effekseer battle animations such as spell bursts and weapon trails. When disabled,
  the `BattleEffects` layer stays dormant so the WebGL runtime never initializes.

Each control operates independently, allowing players to disable specific animations while keeping others. Components like `StarStorm.svelte` and `BattleEventFloaters.svelte` check both legacy `reducedMotion` props and the new granular settings via `getMotionSettings()`.

### System Monitoring & Data Management
Audio volume controls use the `DotSelector` component to render ten selectable levels (0–100%). Gameplay controls that need explanations wrap their labels in the `Tooltip` component for accessible hover and focus hints. System settings include icons for backend health (`activity`), framerate (`gauge`), and data management (`trash-2`, `download`, `upload`).

## Settings Storage & Migration

Settings are stored in `localStorage` with schema versioning for backward compatibility. The system automatically migrates from the old flat `reducedMotion` boolean to the new hierarchical motion settings structure while preserving existing player preferences.

`SettingsMenu.svelte` handles tab selection, LRM configuration, and dispatches `save` and `endRun` events. `SettingsMenu.svelte` receives `backendFlavor` from the page and checks it for `"llm"` to decide whether the LLM tab should appear. When the flavor string omits `"llm"`, the component skips `getLrmConfig()` and hides the model selector and test button.

The Gameplay tab's **End Run** button now attempts to end the current run by ID and falls back to clearing all runs when the ID is missing or the targeted request fails. When the cleanup completes successfully the root page opens a "Run Ended" confirmation overlay so players get positive feedback that their manual termination succeeded.

The Gameplay tab also exposes an **Animation Speed** slider (0.1–2.0×). Adjusting it writes the selected multiplier to settings storage and posts the derived turn pacing (`base_turn_pacing / animationSpeed`) to `/config/turn_pacing` so backend battle pacing matches the UI setting.

The **Skip Battle Review** toggle allows players to bypass the post-battle summary screen and advance directly to the next room. When enabled, the Battle Review overlay is suppressed and the game automatically progresses after battle completion, while still respecting reward handling logic. This setting defaults to `false` to preserve the existing review experience.

## UX Expectations

- All theme and motion controls are keyboard accessible via tab navigation
- Settings changes are auto-saved and persist across sessions
- The legacy "Reduced Motion" checkbox is disabled with helpful text directing users to the granular controls
- Theme changes apply immediately to provide visual feedback
- Motion setting changes take effect immediately for newly created animations
- Settings maintain backward compatibility with existing save data through automatic migration