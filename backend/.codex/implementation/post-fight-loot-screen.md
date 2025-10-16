# Post-fight loot screen staging flow

When a battle ends the loot screen must now treat reward selections as a two
phase process. The player can highlight a card or relic choice, but the
selection is staged until a follow-up confirmation call commits it to the
party. This section documents the backend contract that powers the staging
experience.

## Reward staging payload

The map state (`runs.lifecycle.load_map`) always contains a `reward_staging`
object with three buckets:

```json
{
  "cards": [],
  "relics": [],
  "items": []
}
```

After the player selects a reward, the backend populates the matching bucket
with a serialised entry. For example, choosing a card yields:

```json
{
  "cards": [
    {
      "id": "arc_lightning",
      "name": "Arc Lightning",
      "stars": 3,
      "about": "+255% ATK; every attack chains 50% of dealt damage to a random foe."
    }
  ],
  "relics": [],
  "items": []
}
```

Relic entries expose the stacks the party will hold *after* confirmation so the
UI can preview the post-confirmation state:

```json
{
  "id": "old_coin",
  "name": "Old Coin",
  "stars": 2,
  "stacks": 2,
  "about": "Gain 20% more gold from all sources."
}
```

The staging payload is mirrored into `runs.lifecycle.battle_snapshots` so
reconnecting clients immediately see the staged choice without re-running the
selection logic.

## Progression flags

Because staged rewards are not yet committed, the `awaiting_card` or
`awaiting_relic` flags remain `True` after a selection. `awaiting_next` stays
`False` until the confirmation endpoint applies the staged payload. This keeps
`advance_room` guarded and guarantees the loot screen remains visible across
reconnects.

`reward_progression` is left untouched—`current_step` continues to point at the
pending reward step and `completed` remains unchanged. Consumers should use the
presence of staged entries to drive confirmation UI instead of relying on
`awaiting_next`.

## Client expectations

Frontends should read from `reward_staging` to present the staged card or relic
and block room advancement until the confirmation call succeeds. Confirmation
logic is responsible for applying the staged payload, clearing the bucket, and
flipping the `awaiting_*` flags. Until then the party roster (`Party.cards` and
`Party.relics`) is intentionally unchanged.
