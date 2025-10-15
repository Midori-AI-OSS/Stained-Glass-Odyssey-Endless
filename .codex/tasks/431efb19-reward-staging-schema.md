# Introduce persistent reward staging buckets

## Summary
Design and persist a dedicated reward staging structure alongside the run map so cards, relics, and items can be queued without mutating the active party roster. Focus strictly on the data layer and serialization/backfill work needed to support later lifecycle tasks.

## Requirements
- Extend the run state serialization (`runs` table blobs, `load_run_state`, `save_run_state`, etc.) with a `reward_staging` container split into `cards`, `relics`, and `items` arrays (or comparable keyed structure).
- Ensure staging data is stored with the run map instead of the party blob so reconnect flows can reload staged rewards without polluting `Party.cards` / `Party.relics`.
- Provide backfill/migration helpers that safely initialize the new structure for existing saves and snapshots.
- Document the schema update in `.codex/implementation/post-fight-loot-screen.md` and any other run-state docs that describe reward persistence.

## Out of scope
Do not change service APIs, confirmation flows, or UI payloads yet—those are covered by follow-up tasks.

## Audit notes (2025-02-14)
- Verified new `runs.lifecycle.ensure_reward_staging` normalizes the persisted map payload and backfills existing saves while keeping staged rewards out of `Party` blobs. Also confirmed `_sync_snapshot_reward_staging` mirrors the buckets into in-memory battle snapshots for reconnect flows.
- Confirmed new runs seed `reward_staging` via `run_service` so the map serialization always carries empty `cards`, `relics`, and `items` arrays. Observed documentation updates in `.codex/implementation/post-fight-loot-screen.md` and `.codex/implementation/save-system.md` describing the new structure.
- Exercised targeted regression tests: `uv run pytest tests/test_reward_staging_schema.py`.

requesting review from the Task Master
