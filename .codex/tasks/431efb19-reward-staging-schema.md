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

ready for review
