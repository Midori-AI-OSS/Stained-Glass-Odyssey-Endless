# Card Inventory

`CardInventory.svelte` lists collected cards inside a shared `MenuPanel`. The
menu shows each card's name in a wrapped grid and displays a placeholder message
when no cards are owned. The inventory can be accessed during combat to review
collected cards and their effects. The broader `InventoryPanel.svelte` now also
shows upgrade materials in a Star‑Rail‑style grid with quantity badges and a
detail pane.

Card names, rarities, and descriptions originate from the backend plugins in
`backend/plugins/cards/`. Keep each plugin's `about` text and helper methods
accurate—they power both the in-game inventory and contributor references, so
duplicating the roster here is no longer necessary.

## Testing
- `bun test`
