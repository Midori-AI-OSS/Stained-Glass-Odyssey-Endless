# Reward confirmation payloads

This reference outlines the payloads returned by the reward confirmation and
rollback endpoints introduced with the staging flow. The endpoints live under
`/rewards/<type>/<run_id>/*` and return a consistent shape so clients can update
their local state without re-fetching the full map.

## Confirmation response

`POST /rewards/{card|relic}/<run_id>/confirm`

```json
{
  "reward_staging": {
    "cards": [],
    "relics": [],
    "items": []
  },
  "awaiting_card": false,
  "awaiting_relic": true,
  "awaiting_loot": false,
  "awaiting_next": false,
  "reward_progression": {
    "available": ["card", "relic"],
    "completed": ["card"],
    "current_step": "relic"
  },
  "cards": ["arc_lightning"],
  "next_room": "shop"
}
```

Key fields:

- `reward_staging`: always returned so UIs can clear local staging state.
- `awaiting_*`: reflect the refreshed gating flags. When all are false the
  backend flips `awaiting_next` to `true` to signal room advancement is allowed.
- `reward_progression`: present when additional reward steps remain. The field is
  omitted entirely once the sequence completes.
- `cards` / `relics`: included only for the confirmed reward type so overlays can
  show the updated deck or relic stacks without another `/ui` poll.
- `next_room`: populated when `awaiting_next` becomes `true`.

## Cancellation response

`POST /rewards/{card|relic}/<run_id>/cancel`

```json
{
  "reward_staging": {
    "cards": [],
    "relics": [],
    "items": []
  },
  "awaiting_card": true,
  "awaiting_relic": false,
  "awaiting_loot": false,
  "awaiting_next": false,
  "reward_progression": {
    "available": ["card"],
    "completed": [],
    "current_step": "card"
  }
}
```

- Cancellation never returns the party roster because nothing changed on disk.
- `awaiting_next` is always `false` so the UI keeps the loot overlay open.
- The progression block is reset to the cancelled step so the front-end can
  redisplay the appropriate selection UI.

## Cleanup behaviour

Once a run leaves the reward state (advancing to the next room or ending the
run) `cleanup_battle_state` empties any remaining staging buckets in both the
stored map and the in-memory snapshot. This guarantees confirmation responses
never surface stale staged data on reconnects.
