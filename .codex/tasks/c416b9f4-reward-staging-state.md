# Build a reward staging state separate from the active deck

## Summary
Establish a dedicated staging container for newly awarded cards and relics so their modifiers are queued rather than applied immediately. The state should persist alongside the party record and expose lifecycle hooks for when a player previews, confirms, or cancels a reward.

### Current behaviour to replace
- `select_card` / `select_relic` in `backend/services/reward_service.py` currently call `award_card` / `award_relic` immediately, append the id to `party.cards` or `party.relics`, and flush the whole `Party` back to disk via `save_party` before returning the reward payload. That flow permanently mutates the party, which is why the frontend cannot render "preview only" state today.
- `_run_battle` in `backend/runs/lifecycle.py` stores the resolved reward payload in `battle_snapshots[run_id]` and sets the `awaiting_*` flags plus `reward_progression` on the run map. Advancing the run (`advance_room` in `backend/services/run_service.py`) refuses to move forward until every `awaiting_*` flag is false.
- `save_party` and `load_party` serialise the full party (members, `cards`, `relics`, EXP, etc.) straight into the `runs` table; there is no parallel storage for staged rewards.

### Implementation notes
- Introduce a dedicated staging structure (e.g., `state["reward_staging"] = {"cards": [...], "relics": [...], "items": [...]}`) that is persisted with the run map/state rather than the party blob so staged entries survive reconnects without affecting `Party.cards` or `Party.relics` until confirmed.
- Ensure `battle_snapshots[run_id]` continues to expose the raw reward choices so the frontend overlay logic (see `.codex/implementation/post-fight-loot-screen.md`) keeps working, but augment those snapshots with the staged metadata so that later tasks can render previews without mutating the live party.
- Update the reward lifecycle APIs so that:
  * `choose_card` / `choose_relic` enqueue into the staging record, mark `reward_progression.completed`, and only commit to `Party` + `save_party` when the player confirms the staged set.
  * Confirmation clears the staging bucket and toggles `awaiting_next` exactly once; cancellation removes the staged entry and re-opens the relevant step.
- Revisit battle cleanup helpers (`purge_run_state`, `cleanup_battle_state`) to make sure staged data is cleared when a run terminates or rewinds.

## Deliverables
- Schema or data structure additions that persist pending rewards independently of the active card/relic pools (include migration/backfill logic for existing save blobs).
- Service-level APIs (or updates to `reward_service`) that enqueue rewards into the staging state, expose staged entries over `/ui` + `/rewards/*`, and gate confirmation so `advance_room` still only succeeds once staged rewards are applied or explicitly dismissed.
- Clear lifecycle handling covering preview start, confirmation, rollback/cancellation, and reconnect flows, backed by persistence and concurrency regression tests (cover battle snapshots, map reloads, and `advance_room`).

## Why this matters for players
Players currently receive no feedback at pick time because modifiers only land during the next battle setup. Staging the rewards unlocks immediate previews while keeping the actual party deck untouched until they commit, eliminating surprise stat swings between fights.
