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

`reward_progression` remains in sync with the pending step list—`current_step`
continues to point at the active phase while `available` and `completed`
enumerate the canonical sequence (`drops`, `cards`, `relics`, and optionally
`battle_review`). The backend reconstitutes the structure whenever metadata is
missing by inspecting the staging buckets and `awaiting_*` flags, so clients can
trust the payload even after reconnects. Consumers should use the presence of
staged entries to drive confirmation UI instead of relying solely on
`awaiting_next`.

## Client expectations

Frontends should read from `reward_staging` to present the staged card or relic
and block room advancement until the confirmation call succeeds. Confirmation
logic is responsible for applying the staged payload, clearing the bucket, and
flipping the `awaiting_*` flags. Until then the party roster (`Party.cards` and
`Party.relics`) is intentionally unchanged.

## Confirmation workflow

Staged rewards are committed through the dedicated confirmation endpoints:

- `POST /rewards/card/<run_id>/confirm`
- `POST /rewards/relic/<run_id>/confirm`

Each endpoint consumes the staged payload for the requested reward type. A
per-run asyncio lock (`runs.lifecycle.reward_locks[run_id]`) guarantees that
confirmation, cancellation, and selection calls execute serially so the staged
payload is applied at most once even if the UI retries the request. The server
appends the staged card or relic to the saved party, clears the staging bucket,
and updates the reward progression sequence. When no further rewards are
pending the backend flips `awaiting_next` to `True` so the room can advance.
The JSON response mirrors the updated state and includes the current party deck
or relic list alongside the refreshed `reward_staging` payload.

The confirmation response also exposes an `activation_record` describing the
commit event:

```json
{
  "activation_record": {
    "activation_id": "0fe817fb-...",
    "bucket": "cards",
    "activated_at": "2025-03-14T05:09:27.224310+00:00",
    "staged_values": [
      {
        "id": "arc_lightning",
        "name": "Arc Lightning",
        "stars": 3,
        "about": "+255% ATK; every attack chains 50% of dealt damage to a random foe."
      }
    ]
  },
  "reward_activation_log": [
    {
      "activation_id": "0fe817fb-...",
      "bucket": "cards",
      "activated_at": "2025-03-14T05:09:27.224310+00:00"
    }
  ]
}
```

`reward_activation_log` is persisted with the run and mirrored into battle
snapshots so reconnecting clients can audit prior confirmations. Only the most
recent twenty activations are retained to bound storage.

Clients can roll back a staged choice with:

- `POST /rewards/card/<run_id>/cancel`
- `POST /rewards/relic/<run_id>/cancel`

Cancellation removes the staged entry, reopens the matching progression step,
and ensures `awaiting_next` stays `False`. Downstream UIs should respond by
redisplaying the available choices and prompting the player to select again.

`advance_room` now verifies both the `awaiting_*` flags **and** that every
`reward_staging` bucket is empty. Attempts to advance while a staged reward
remains (even if `awaiting_card`/`awaiting_relic` has been cleared) produce a
`400` error: “pending rewards must be collected before advancing.” Frontends
must always confirm or cancel staged entries before requesting the next room.

## Cleanup guarantees

`runs.lifecycle.cleanup_battle_state` now clears any non-empty staging buckets
whenever a run leaves the reward state (either because the run ended or because
all confirmations completed). This prevents reconnects from surfacing stale
staging data after the player advances to the next room or abandons the run.
