# Player Upgrade Endpoint

`GET /players/<id>/upgrade` returns the current upgrade level for the
specified character, the full inventory of element-based upgrade items, and a
per-stat material breakdown. Each entry in `next_costs` exposes the total
1★ units (`units`) alongside a `breakdown` map keyed by material id (such as
`fire_2`, `fire_1`) so clients can surface mixed-star requirements and echo
the exact payload back to the server when requesting an upgrade.

`POST /players/<id>/upgrade` consumes 20×4★ (or 100×3★/500×2★/1000×1★) items
matching the character's damage type and increments their stored level. Each
rank boosts HP, ATK, and DEF by 5% and persists in the `player_upgrades`
table. Item counts live in `upgrade_items`.

## Testing
- `uv run pytest backend/tests/test_player_upgrade.py`
