# Relic Inventory

`RelicInventory.svelte` uses `MenuPanel` to show a grid of relic names. If no
relics are held, the menu reports an empty inventory. The inventory can be
accessed during combat to review collected relics and their effects. Upgrade
materials now appear alongside cards and relics in `InventoryPanel.svelte`,
rendered in a color‑coded grid with quantity badges and a detail pane.

Relic entries display their stack count and expose their description as tooltip
text via the `about` field returned by the backend. All relic copy, star ranks,
and behaviour details live in the plugin modules under `backend/plugins/relics/`.
Treat those modules as the canonical reference and keep the `about` string and
`describe(stacks)` output authoritative. This file now focuses on the UI wiring
only.

## Testing
- `bun test`
