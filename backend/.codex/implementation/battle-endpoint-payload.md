# Reward confirmation payload reference

The reward staging flow exposes a trio of endpoints beneath
`/rewards/<reward_type>/<run_id>/…` so clients can confirm or cancel staged
choices without polling the entire `/ui` payload. This guide documents the
responses returned by those handlers.

- `POST /rewards/<reward_type>/<run_id>/confirm`
- `POST /rewards/<reward_type>/<run_id>/cancel`
- `POST /rewards/loot/<run_id>` (acknowledges auto-awarded drops)

`<reward_type>` accepts `card`, `cards`, `relic`, `relics`, `item`, and `items`.
`reward_type` is normalised to the canonical staging bucket internally so the
same contract applies regardless of the alias supplied by the client.

## Confirmation response

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
    "available": ["cards", "relics"],
    "completed": ["cards"],
    "current_step": "relics"
  },
  "cards": ["arc_lightning"],
  "next_room": "shop",
  "activation_record": {
    "activation_id": "2f6dbd25-...",
    "bucket": "cards",
    "activated_at": "2025-03-14T05:09:27.224310+00:00",
    "staged_values": [
      {
        "id": "arc_lightning",
        "name": "Arc Lightning",
        "stars": 3
      }
    ]
  },
  "reward_activation_log": [
    {
      "activation_id": "2f6dbd25-...",
      "bucket": "cards",
      "activated_at": "2025-03-14T05:09:27.224310+00:00"
    }
  ]
}
```

Key points:

- `reward_staging` always reflects the emptied staging buckets so UIs can clear
  their local previews immediately after confirmation.
- `awaiting_*` exposes the refreshed gating flags. When all three are `false` the
  backend sets `awaiting_next` to `true` and, when possible, includes the upcoming
  `next_room` type.
- `reward_progression` is present when further reward steps remain. The field is
  removed entirely once the sequence finishes.
- `cards` or `relics` appear only when that bucket was confirmed; there is no
  `items` array because staged loot is merged directly into `party.items`.
- `activation_record` captures the single confirmation event, including a copy of
  the staged payload. This is echoed at the top of `reward_activation_log`.
- `reward_activation_log` stores the twenty most recent confirmation events so
  clients and QA can audit duplicate submissions without replaying history from
  `/ui`.

Confirming an `item` or `items` bucket follows the same contract. The `bucket`
field in both activation structures changes to `"items"` and `awaiting_loot`
flips to `false` once the drops are committed.

## Cancellation response

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
    "available": ["cards"],
    "completed": [],
    "current_step": "cards"
  }
}
```

Cancellation clears the requested bucket and reopens the progression step while
keeping `awaiting_next` set to `false`. No activation metadata is returned
because nothing changed on disk. After the response the battle snapshot mirrors
the updated staging payload, ensuring reconnecting clients see the cleared
selection immediately.

## Loot acknowledgement response

`POST /rewards/loot/<run_id>` returns only the upcoming room hint because the
party state is unchanged:

```json
{
  "next_room": "boss"
}
```

The acknowledgement endpoint is only used for automatically granted drops that
skipped the staging UI. Manual loot confirmations should continue to use the
standard `confirm` and `cancel` routes above.

## Advance room progression response

When rewards remain after a step completes (for example when a battle review is
still queued), `/ui?action=advance_room` no longer advances the map immediately.
Instead it returns the refreshed progression payload so the UI can transition to
the next reward phase without a full `/ui` poll:

```json
{
  "progression_advanced": true,
  "current_step": "battle_review",
  "reward_progression": {
    "available": ["cards", "battle_review"],
    "completed": ["cards"],
    "current_step": "battle_review"
  },
  "awaiting_card": false,
  "awaiting_relic": false,
  "awaiting_loot": false,
  "awaiting_next": false
}
```

The `reward_progression` field persists in every `/ui` and advance-room payload
until the sequence fully resolves, mirroring the confirmation endpoints above.

## Telemetry and monitoring

Reward confirmation routes also emit game-action telemetry so operations can
spot suspicious duplicate submissions. Every successful confirmation writes a
`confirm_<reward_type>` record through `tracking.service.log_game_action`, and
requests that arrive with an empty staging bucket trigger a
`confirm_<bucket>_blocked` entry.

- **Action type:** The suffix uses the canonical bucket name (`cards`, `relics`,
  or `items`) regardless of the alias supplied to the endpoint.
- **Details payload:**
  - `bucket` repeats the canonical bucket name so downstream log processors can
    group the signals without parsing the action type.
  - `reason` currently reports `"empty_staging"`, distinguishing duplicate
    submissions from future guardrails.
  - `awaiting` snapshots the `awaiting_*` flags to help triage whether the UI is
    still prompting the player (`true`) or the flow completed before the retry
    arrived (`false`).

### Operational guidance

- **Live alerting:** Surface `confirm_%_blocked` counts in whichever metrics
  sink ingests `game_actions`. Spikes indicate players or automation are
  re-submitting a confirmation without staging a new reward.
- **On-demand investigations:** Use the tracking database to pull the raw
  records when debugging reports. For example:

  ```sql
  SELECT action_type, run_id, room_id, ts, details_json
    FROM game_actions
   WHERE action_type LIKE 'confirm_%_blocked'
ORDER BY ts DESC
   LIMIT 20;
  ```

  The JSON payload mirrors the fields described above, giving support staff
  enough context to reconcile the player's UI state with the guardrail that
  rejected the confirmation.
