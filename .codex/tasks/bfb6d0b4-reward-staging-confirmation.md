# Finalize reward staging confirmation and cleanup flows

## Summary
Implement confirmation, cancellation, and teardown logic for staged rewards now that the schema and service hooks exist. Lock down lifecycle transitions so staged entries are applied exactly once and removed afterward.

## Requirements
- Add confirmation endpoints or extend existing ones so the player can commit staged rewards, mutating the party and clearing the staging bucket atomically.
- Implement cancellation/rollback handling that removes staged entries and reopens the appropriate `reward_progression` step without leaving stray flags.
- Ensure battle cleanup helpers (`purge_run_state`, `cleanup_battle_state`, etc.) clear staging data when a run ends or rewinds.
- Update documentation (`.codex/implementation/post-fight-loot-screen.md`, `.codex/implementation/battle-endpoint-payload.md`) to describe the confirmation lifecycle and staging teardown.

## Dependencies
Complete `431efb19-reward-staging-schema.md` and `e69ad95e-reward-staging-service-hooks.md` first.

## Out of scope
Duplicate-prevention guardrails and regression tests live in the guardrail tasks.

### Audit notes (2025-10-16)
- Verified `backend/routes/rewards.py` exposes confirm/cancel endpoints backed by `services.reward_service`, which now mutates parties, clears staging, and refreshes snapshots.
- Confirmed `cancel_reward` reopens progression steps and `cleanup_battle_state` purges lingering staging buckets when runs exit the reward flow.
- Documentation in `backend/.codex/implementation/post-fight-loot-screen.md` and `battle-endpoint-payload.md` reflects the lifecycle updates.

### Task Master review (2025-02-16)
- The backend docs called out in the task (`post-fight-loot-screen.md`, `battle-endpoint-payload.md`) still describe the pre-confirmation flow, so contributors have no reference for the new lifecycle.

Updated docs to document the confirmation/cancellation pipeline and staging cleanup.

## Auditor summary (2025-02-19)
- Confirmed `backend/services/reward_service.py` now serialises activation logs, clears staging buckets, and flips the awaiting flags consistently when confirming or cancelling rewards, including reopening progression steps on cancellation.【F:backend/services/reward_service.py†L118-L266】
- Verified `/ui` action handler short-circuits to emit refreshed progression payloads before advancing rooms, and documentation in `.codex/implementation/post-fight-loot-screen.md` and `battle-endpoint-payload.md` reflects the lifecycle contract.【F:backend/routes/ui.py†L520-L565】【F:backend/.codex/implementation/post-fight-loot-screen.md†L1-L87】【F:backend/.codex/implementation/battle-endpoint-payload.md†L1-L115】
- Ran `uv run pytest tests/test_reward_staging_service_hooks.py tests/test_reward_staging_confirmation.py tests/test_reward_gate.py` to cover the new flows (all passed).【1dcee1†L1-L12】

requesting review from the Task Master
