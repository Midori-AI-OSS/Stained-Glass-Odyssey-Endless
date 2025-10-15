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
