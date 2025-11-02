# Main Menu

The home screen presents a high-contrast column layout with the run action grid on the right rail and the viewport banner and PartyPicker shell on the left. Primary actions are rendered through `RunButtons.svelte`, which builds a single list of Lucide-powered buttons rather than the old 2×3 grid.

## Actions
- **Run** — opens the run chooser. If no active runs exist it launches the PartyPicker step so the lineup can be reviewed before map generation. Existing runs skip directly to resume.
- **Warp** — opens the gacha/pulls overlay (`openPulls`). Disabled while a battle is active.
- **Inventory** — surfaces the in-run inventory overlay so players can inspect cards, relics, and upgrade materials between encounters.
- **Battle Review** — opens the battle-review menu overlay, allowing players to revisit previous fights.
- **Guidebook** — navigates to the reference overlay with tabs for damage types, ultimates, UI notes, shops, mechs, and passives.
- **Settings** — launches the settings overlay with audio sliders, Reduced Motion, and End Run controls.

Quick links for **Feedback**, **Discord**, and the project **Website** follow the primary actions and open external pages in a new window. These links remain available during runs so testers can report issues without leaving the game.

## Layout Notes
- The PartyPicker no longer has a dedicated "Party" button on the home menu; editing happens inside the Run flow only.
- Inventory access still mirrors the top-left NavBar entry so players can inspect loot without starting a run.
- Button spacing and keyboard navigation should remain consistent after removing the legacy Party entry.

## Testing
- `bun test tests/run-wizard-flow.vitest.js`
- `bun test tests/shopmenu.test.js`
