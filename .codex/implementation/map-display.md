# Map Display

`MapDisplay.svelte` replaces the old `RunMap` and wraps the run's floor layout
in `MenuPanel`. The list is ordered with the current room at the bottom and the
boss at the top so the path reads upward. Each room is rendered as a
stained-glass button with a `lucide-svelte` icon matching its type (battle,
shop, boss, or unknown). The component now shows a party preview above
the map, using `assetLoader` to pull character portraits for selected allies.
Only the current room is clickable and fully opaque; upcoming rooms stay
visible but are greyed out and disabled. The map slices to the last four rooms
using `map.slice(-4)` to cut extra DOM nodes, and each party portrait tint comes from
`getElementColor` so damage types stand out. The component emits a `select`
event when the player chooses the current room.

## Testing
- `bun test frontend/tests/mapdisplay.test.js`
