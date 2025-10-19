# Post-fight loot confirmation pipeline

The loot overlay now uses an explicit stage-and-confirm lifecycle so that
clients can preview rewards without mutating the saved party until the player
commits their choice. This document describes how the backend routes and
lifecycle helpers co-ordinate that pipeline.

## Staging buckets

`runs.lifecycle.ensure_reward_staging` guarantees that the map state always
contains a `reward_staging` object with three buckets:

```json
{
  "cards": [],
  "relics": [],
  "items": []
}
```

Whenever the player highlights a card or relic, the selection endpoints
(`POST /rewards/cards/<run_id>` and `POST /rewards/relics/<run_id>`) populate the
matching bucket with a serialised preview of what will be committed after
confirmation. The payload mirrors the structures returned from
`autofighter.cards.instantiate_card` and `autofighter.relics.instantiate_relic`
so the UI can show the post-confirmation state—including preview metadata—without
writing to disk. Item drops follow the same convention: loot is staged in the
`items` bucket until it is acknowledged.

The staging payload is also copied into `runs.lifecycle.battle_snapshots` so
reconnecting clients recover the staged state without replaying the selection
flow.

## Progression flags and gating

Because staged rewards are not yet applied, the map keeps the
`awaiting_card`, `awaiting_relic`, and `awaiting_loot` flags set to `True` until
the relevant confirmation call succeeds. `ensure_reward_progression` rebuilds
the canonical `reward_progression` structure (`drops → cards → relics →
battle_review`) whenever metadata is missing so the overlay can rely on the
returned state even after reconnects. `advance_room` now verifies both that all
`awaiting_*` flags are cleared **and** that every staging bucket is empty; any
attempt to advance with lingering staged rewards returns a `400` error telling
the client to finish collecting rewards first.

## Confirmation stage

Staged rewards are committed through `POST /rewards/<reward_type>/<run_id>/confirm`
where `<reward_type>` may be `card`, `cards`, `relic`, `relics`, `item`, or
`items`. Each request executes under the run-specific asyncio lock in
`runs.lifecycle.reward_locks` to guarantee serial execution of selection,
confirmation, and cancellation calls. The confirmation handler performs the
following steps:

1. Validate that the requested bucket contains staged values.
2. Apply the staged payload to the party:
   - Cards append the staged card identifier to `party.cards` (if it is not
     already present).
   - Relics append the relic identifier to `party.relics`, preserving stacks.
   - Items merge the staged item dictionaries into `party.items`.
3. Clear the staging bucket and flip the corresponding `awaiting_*` flag to
   `False`.
4. Call `_update_reward_progression` so the completed step moves from
   `available` to `completed`.
5. Set `awaiting_next` to `True` only when **all** buckets and gating flags are
   cleared; otherwise it remains `False` so the overlay stays visible.
6. Append an `activation_record` to the persisted `reward_activation_log`,
   trimming the list to the 20 most recent confirmations.
7. Persist the map and party, refresh the battle snapshot, and emit a
   `confirm_<reward_type>` game-action log.

The JSON response always includes the refreshed `reward_staging` payload, the
four gating flags, the activation record, and the full activation history. When a
card or relic is confirmed the payload also contains the updated `cards` or
`relics` list so the client can refresh the deck overlay without another `/ui`
poll. If `awaiting_next` becomes `True`, the response adds a `next_room` field
with the upcoming room type.

## Cancellation stage

Players can roll back a staged choice through
`POST /rewards/<reward_type>/<run_id>/cancel`. The handler clears the requested
bucket, marks the corresponding `awaiting_*` flag as `True`, and reopens the
reward step via `_update_reward_progression`. `awaiting_next` is forced to
`False` so the loot overlay remains active, and the refreshed staging payload is
mirrored into the battle snapshot before the response is sent back to the client.
The cancellation payload mirrors the confirmation shape minus the activation
fields because nothing was committed to disk.

## Loot acknowledgement

Auto-awarded drops that do not go through the manual confirmation flow use
`POST /rewards/loot/<run_id>` (`acknowledge_loot`) to clear `awaiting_loot` and
advance the progression sequence. The acknowledgement response contains only the
`next_room` hint because the party state remains unchanged.

## Cleanup guarantees

`runs.lifecycle.cleanup_battle_state` removes any non-empty staging buckets when
a run exits the reward flow—either because the player abandoned the run or all
confirmations finished. This prevents reconnects from resurfacing stale staged
values after the room advances.
