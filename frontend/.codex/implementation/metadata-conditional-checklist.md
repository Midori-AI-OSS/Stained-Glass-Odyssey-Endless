# Metadata Conditional Audit Checklist

## Replacement summary

- Mimic portrait loading now relies on `ui.portrait_pool = "player_mirror"`
  from `/players` metadata instead of comparing `id === 'mimic'` in
  `assetRegistry.js`.
- Lady Echo portrait randomisation uses `ui.portrait_pool = "player_gallery"`
  so the asset registry treats her like a player without checking
  `id === 'lady_echo'`.
- Party Picker filtering consumes `ui.non_selectable` from `/players` metadata
  to hide the Mimic, replacing the `entry.id === 'mimic'` fallback.
- Loot overlays (`OverlayHost.svelte` / `RewardOverlay.svelte`) prefer
  `item.ui.label` provided by the backend instead of hard-coding
  `item.id === 'ticket'`.

## Testing performed

- `uv run pytest backend/tests/test_player_ui_metadata.py`
- `uv run pytest backend/tests/test_loot_summary.py`
- `bun x vitest run` *(still fails: upstream Svelte/Vitest integration lacks loader context; manual component QA required until a lightweight transform is added)*
