# Post-Fight Loot Screen

After a battle concludes the frontend polls `roomAction(runId, 'battle', 'snapshot')` until the snapshot includes a `loot` object summarizing gold earned and any reward choices. `OverlayHost.svelte` keeps `BattleView.svelte` mounted during this polling and only opens `RewardOverlay.svelte` once the `loot` data arrives and combat is flagged complete. Players must resolve any card or relic picks and then press the **Next Room** button, which calls `/run/<id>/next` to advance the run.

## Reward staging persistence
- The run map JSON stored in the `runs.map` column now includes a `reward_staging` object with `cards`, `relics`, and `items` arrays. These buckets capture unconfirmed selections so reconnecting clients can resume the overlay without mutating the live party loadout. Each staged entry embeds a `preview` payload describing the pending stat changes and any trigger hooks so the UI can narrate the reward before confirmation.
- `runs.lifecycle.load_map` backfills this structure for older saves and mirrors the data into any in-memory battle snapshot (`battle_snapshots[run_id]`) so `/ui` and `/map/<id>` consumers receive the same staged entries.
- `runs.lifecycle.save_map` always normalizes the `reward_staging` payload before writing so downstream services can append staged rewards without defensive guards. Future confirmation flows will clear the buckets once rewards are committed.

## Single-confirm guardrails
- `services.reward_service.confirm_reward` acquires a per-run `reward_locks[run_id]` mutex before mutating staging data, ensuring duplicate HTTP calls or reconnects cannot race each other while a confirmation is in flight.
- On success the targeted staging bucket is cleared, the appropriate `awaiting_*` flags are flipped off, and `awaiting_next` is only raised once every bucket is empty. Failed or replayed confirmations raise an error because the staging list is empty.
- Each activation appends a record to `state["reward_activation_log"]` with a generated `activation_id`, timestamp, bucket name, and the committed payload. Snapshots mirror this log so the frontend can surface audit breadcrumbs and the backend retains the last 20 activations for debugging.
- `services.run_service.advance_room` now blocks when any staging bucket still contains entries via `runs.lifecycle.has_pending_rewards`, preventing map progression until the overlay has been fully resolved.

## Testing
- `uv run pytest tests/test_loot_summary.py`
- `bun test`
