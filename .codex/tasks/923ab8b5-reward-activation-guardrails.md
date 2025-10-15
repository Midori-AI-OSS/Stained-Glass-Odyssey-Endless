# Guarantee single activation and solid tests for reward staging

## Summary
Once a player accepts a staged reward, we need deterministic activation and guardrails that prevent duplicate applications or lingering staged entries. This task covers the confirmation pipeline, cleanup, and regression tests around both battle setup and backtracking scenarios.

### Where the guardrails must hook in
- The run map keeps `awaiting_card`, `awaiting_relic`, `awaiting_loot`, and `reward_progression` (see `_run_battle` in `backend/runs/lifecycle.py`). `advance_room` in `backend/services/run_service.py` currently refuses to progress if any `awaiting_*` flag is still true, but it has no awareness of staged-but-unapplied data.
- `reward_service.select_card` / `select_relic` mutate the party immediately today. After staging lands, these entry points must atomically flip `reward_progression` from `current_step -> completed` while keeping the staged payload until the player confirms.
- `battle_snapshots[run_id]` mirrors the latest reward state for reconnecting clients, and `cleanup_battle_state` / `purge_run_state` tear down live battle context. Guardrails have to ensure staged records survive reconnects but disappear once applied or cancelled.
- UI flows such as `backend/tests/test_reward_gate.py` simulate choose/advance loops; expand those tests (and add new ones) so they cover race conditions like double-submit, reconnect, or manual `/rewards/cards` retries.

## Deliverables
- Update reward activation logic so staged entries are applied exactly once and cleared afterward, even across reconnects or retries.
- Add automated tests covering double-accept attempts, battle setup integration, cancellation/rollback flows, and reconnect scenarios (battle snapshot reload, `/ui` polling while a staged item exists, etc.).
- Instrument logging or metrics to flag unexpected duplicate activations for live ops follow-up.
- Ensure `advance_room` and any other callers that depend on `awaiting_*` also verify the staging bucket is empty before allowing progression, and document the guardrail behaviour in `.codex/implementation/battle-endpoint-payload.md` / `.codex/implementation/post-fight-loot-screen.md`.

## Why this matters for players
Without strong guardrails, players risk losing rewards or gaining unintended double buffs when staging is introduced. Reliable activation keeps progression fair and predictable, maintaining trust in the reward system.
