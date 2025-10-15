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
