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
