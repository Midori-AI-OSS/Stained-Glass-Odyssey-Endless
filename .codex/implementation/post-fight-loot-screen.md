# Post-Fight Loot Screen

After a battle concludes the frontend polls `roomAction(runId, 'battle', 'snapshot')` until the snapshot includes a `loot` object summarizing gold earned and any reward choices. `OverlayHost.svelte` keeps `BattleView.svelte` mounted during this polling and only opens `RewardOverlay.svelte` once the `loot` data arrives and combat is flagged complete. Players must resolve any card or relic picks and then press the **Next Room** button, which calls `/run/<id>/next` to advance the run.

## Reward staging persistence
- The run map JSON stored in the `runs.map` column now includes a `reward_staging` object with `cards`, `relics`, and `items` arrays. These buckets capture unconfirmed selections so reconnecting clients can resume the overlay without mutating the live party loadout.
- `runs.lifecycle.load_map` backfills this structure for older saves and mirrors the data into any in-memory battle snapshot (`battle_snapshots[run_id]`) so `/ui` and `/map/<id>` consumers receive the same staged entries.
- `runs.lifecycle.save_map` always normalizes the `reward_staging` payload before writing so downstream services can append staged rewards without defensive guards. Future confirmation flows will clear the buckets once rewards are committed.

## Testing
- `uv run pytest tests/test_loot_summary.py`
- `bun test`
