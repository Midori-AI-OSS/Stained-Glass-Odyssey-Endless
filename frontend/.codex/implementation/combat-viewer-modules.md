# Combat Viewer Modules

`CombatViewer.svelte` has been decomposed into smaller parts:

- `components/combat-viewer/PartyView.svelte` renders the list of party members.
- `components/combat-viewer/FoeView.svelte` renders opposing foes.
- `components/combat-viewer/HpStatus.svelte` displays a character's HP percentage using helpers from `battle/shared.js`.

The shared helper `battle/shared.js` currently exposes `hpPercent` for computing health ratios.
