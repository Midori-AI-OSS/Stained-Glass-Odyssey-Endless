# Player Roster Metadata

`GET /players` continues to return the complete roster for the party picker, but
each entry now includes a `ui` object with hints consumed by the WebUI:

```json
{
  "id": "mimic",
  "name": "Mimic",
  "stats": { "gacha_rarity": 0, "hp": 1000, ... },
  "ui": {
    "non_selectable": true,
    "portrait_pool": "player_mirror",
    "flags": ["non_selectable"]
  }
}
```

- `non_selectable` hides roster entries regardless of `gacha_rarity` (the Mimic
  remains excluded even if upstream data lacks rarity values).
- `portrait_pool` nudges the asset registry: `player_mirror` reuses the player's
  portrait gallery while `player_gallery` randomises from the shared player pool
  without special-casing ids such as `lady_echo`.
- `flags` echoes the boolean hints so telemetry and debugging can rely on a
  single field.

The metadata is generated via `PlayerBase.get_ui_metadata()`, which subclasses
can extend by setting `ui_portrait_pool`, `ui_non_selectable`, or a custom
`ui_metadata` dict. This keeps frontend logic agnostic of hard-coded ids and
lets new roster rules ship with backend plugins.
