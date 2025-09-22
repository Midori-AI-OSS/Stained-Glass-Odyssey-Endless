# Options Menu

The Options submenu lets players adjust audio levels, presentation, system behaviour, and gameplay automation. Controls appear under **Audio**, **UI**, **System**, and **Gameplay** headings and use a two-column grid with labels and icons on the left and interactive controls on the right. Rows highlight on hover for clarity.

## Controls

- **Sound Effects Volume**
  - Ten-dot selector adjusting sound effect levels in 10% increments.
  - Component: `DotSelector`
  - Lucide icon: `volume-2`
  - Label: `SFX Volume`
  - Tooltip: `Adjust sound effect volume.`

- **Music Volume**
  - Ten-dot selector adjusting background music levels.
  - Component: `DotSelector`
  - Lucide icon: `music`
  - Label: `Music Volume`
  - Tooltip: `Adjust background music volume.`

- **Voice Volume**
  - Ten-dot selector adjusting voice levels.
  - Component: `DotSelector`
  - Lucide icon: `mic`
  - Label: `Voice Volume`
  - Tooltip: `Adjust voice volume.`

- **Theme Palette**
  - Select box for switching between predefined palettes or custom mode.
  - Component: `UISettings`
  - Lucide icon: `palette`
  - Tooltip: `Choose a visual theme for the game.`

- **Custom Accent** *(Custom theme only)*
  - Native color input to set accent colour.
  - Component: `UISettings`
  - Lucide icon: `eye`
  - Tooltip: `Custom accent colour for the theme.`

- **Background Mode**
  - Select box switching between rotating, static, or custom backgrounds.
  - Component: `UISettings`
  - Lucide icon: `eye`
  - Tooltip: `How background images are displayed.`

- **Static Background** *(Static mode only)*
  - Select box listing curated cityscape assets.
  - Component: `UISettings`
  - Lucide icon: `eye`
  - Tooltip: `Choose a static background image.`

- **Custom Background** *(Custom mode only)*
  - File picker for uploading a custom background asset.
  - Component: `UISettings`
  - Lucide icon: `eye`
  - Tooltip: `Upload a custom background image.`

- **Global Reduced Motion**
  - Toggle respecting OS preferences while enabling accessibility options.
  - Component: `UISettings`
  - Lucide icon: `move`
  - Tooltip: `Master switch for reduced motion.`

- **Disable Floating Damage**
  - Toggle disabling floating combat numbers and popups.
  - Component: `UISettings`
  - Lucide icon: `move`
  - Tooltip: `Disable floating damage numbers.`

- **Disable Portrait Glows**
  - Toggle removing animated portrait outlines.
  - Component: `UISettings`
  - Lucide icon: `move`
  - Tooltip: `Disable glowing effects around character portraits.`

- **Simplify Overlay Transitions**
  - Toggle simplifying modal and overlay animations.
  - Component: `UISettings`
  - Lucide icon: `move`
  - Tooltip: `Use simpler transitions for overlays.`

- **Disable Star Storm**
  - Toggle disabling animated background particle effects.
  - Component: `UISettings`
  - Lucide icon: `move`
  - Tooltip: `Disable the animated background star storm effect.`

- **Backend Health**
  - Badge shows backend status with latency ping.
  - Lucide icon: `activity`
  - Tooltip: `Backend health and network latency.`

- **Framerate**
  - Select box limiting server polling frequency.
  - Lucide icon: `gauge`
  - Tooltip: `Limit server polling frequency.`
- **Reduced Motion (Legacy)**
  - Read-only indicator mirroring the UI tab's global setting.
  - Lucide icon: `move`
  - Tooltip: `Use UI tab controls for motion settings.`
- **Show Action Values**
  - Toggle that reveals numeric action values in the turn order UI.
  - Tooltip component: `Tooltip` with text `Display numeric action values in the turn order.`

- **Full Idle Mode**
  - Toggle that automates reward selection and room progression.
  - Tooltip: `Automate rewards and room progression.`

- **Animation Speed**
  - Slider that scales the global `TURN_PACING` for all actions.
  - Tooltip: `Adjust battle animation pacing.`

- **Wipe Save Data**
  - Button that clears all save records after confirmation.
  - Lucide icon: `trash-2`
  - Tooltip: `Clear all save data.`
  - Behavior: also clears all frontend client storage (localStorage, sessionStorage, IndexedDB), deletes CacheStorage entries, unregisters service workers, and then forces a full page reload so stale roster or party data cannot persist.

- **Backup Save Data**
  - Button that downloads an encrypted snapshot of save tables.
  - Lucide icon: `download`
  - Tooltip: `Download encrypted save backup.`

- **Import Save Data**
  - File picker that uploads an encrypted backup and restores it if valid.
  - Lucide icon: `upload`
  - Tooltip: `Import encrypted save backup.`

- **Autocraft**
  - Toggle that automatically crafts materials when possible.
  - Label: `Autocraft`
  - Tooltip: `Automatically craft materials when possible.`
  - Behavior: updates the backend via `/gacha/auto-craft` and stays in sync with the Crafting menu toggle.

- **End Current Run**
  - Button that terminates the active run.
  - Lucide icon: `power`
  - Tooltip component: `Tooltip` with text `End the current run.`

## Guidelines

- Each control uses the shared grid layout and hover transitions from `settings-shared.css`.
- Controls must include Lucide icons where specified and accessible tooltips via `title` or `Tooltip` component.
- Changes take effect immediately and should persist between sessions.
- For turn order debugging, enable [Action Value Display](action-value-display.md).
