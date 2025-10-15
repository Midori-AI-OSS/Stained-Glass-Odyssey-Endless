# Route reward selection through staging service hooks

## Summary
Update the reward service and run lifecycle so card/relic selections enqueue into the staging container created by the schema task. This work wires staging into existing flows without yet handling confirmation cleanup logic.

## Requirements
- Modify `reward_service.select_card` / `select_relic` (and any item variants) to append chosen rewards into the new staging bucket while leaving `Party.cards` and `Party.relics` untouched.
- Update run progression flags (`awaiting_card`, `awaiting_relic`, `reward_progression`) so they reflect the staged-but-unconfirmed state.
- Ensure `battle_snapshots[run_id]` mirrors staged entries for reconnecting clients and API consumers.
- Adjust REST/socket payloads (`/ui`, `/rewards/cards`, `/rewards/relics`, etc.) to expose staged rewards without committing them to the live party yet.
- Capture the lifecycle expectations in `.codex/implementation/post-fight-loot-screen.md` so future tasks know how staging data is surfaced.

## Dependencies
Complete `431efb19-reward-staging-schema.md` first so the persistence layer is ready.

## Out of scope
Confirmation/cancellation cleanup and duplicate-prevention guardrails belong to follow-up tasks.


## Auditor notes (2025-10-15)
- Ran `uv run pytest tests/test_reward_staging_service_hooks.py`; both regression tests fail because rewards are applied directly to the party instead of remaining staged.
- `reward_service.select_card` still calls `award_card`, so the party deck gains the selected card immediately, violating the staging requirement.
- `reward_service.select_relic` also calls `award_relic`, increasing the stack count and mutating the party, which breaks the staged-only contract.
- Please update the reward flows so selections only populate `reward_staging`, keep the live party untouched, and adjust the tests/docs accordingly.
