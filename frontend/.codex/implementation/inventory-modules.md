# Inventory Modules

`Inventory.svelte` now delegates rendering to dedicated subcomponents:

- `components/inventory/CardView.svelte` lists collected cards.
- `components/inventory/RelicView.svelte` lists relics.
- `components/inventory/MaterialsPanel.svelte` shows upgrade materials using icons resolved by `systems/materialAssetLoader.js`.

Shared helper `materialAssetLoader.js` centralizes material icon lookups and error handling for missing assets.
