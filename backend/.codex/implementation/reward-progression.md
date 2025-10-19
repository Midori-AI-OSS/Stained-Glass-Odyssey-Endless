# Reward progression and room advancement

The map state blocks advancing to the next room while any post-battle rewards remain unresolved. Three boolean flags gate this progression:

- `awaiting_card` – set when a card reward is offered. If the battle yields no card, this flag stays `False` and does not block advancement.
- `awaiting_relic` – set when a relic reward is pending. Runs without relic drops leave this flag `False`.
- `awaiting_loot` – reserved for manual loot flows. The backend currently auto-collects gold and similar drops, so this flag is usually `False`.

`advance_room` refuses to progress while any of these flags are `True`. The UI action handler returns an HTTP 400 error when a client attempts to advance with pending rewards, and the `run_service.advance_room` function raises a `ValueError` so direct calls cannot bypass the restriction.

Reward sequences also use a `reward_progression` structure to represent the
remaining post-battle phases. The payload always exposes `available`,
`completed`, and `current_step` keys and the step identifiers are normalised to
the canonical order: `drops` → `cards` → `relics` → `battle_review`. Whenever a
run is awaiting loot, cards, relics, or the battle review overlay, the backend
ensures `reward_progression` is populated so the frontend can render the correct
phase without falling back to legacy flags. The helper automatically backfills
missing metadata by inspecting the `awaiting_*` flags and staged reward buckets
and persists the structure until every step is completed, at which point the
field is removed and `awaiting_next` is set.

## Reward staging

Selected rewards are now staged in the map state before they are committed to the
party. The `reward_staging` dictionary mirrors buckets for cards, relics, and
items. When a player chooses a card or relic the backend appends a serialized
entry to the appropriate bucket instead of mutating the party immediately.

Because staged rewards are not yet confirmed the original `awaiting_*` flags are
left `True` until a follow-up confirmation API applies the staged payload. This
keeps room advancement blocked and ensures reconnecting clients still present a
confirmation overlay. Downstream code must rely on `reward_staging` to surface
the selected reward while continuing to treat the party roster as unchanged until
confirmation succeeds.
