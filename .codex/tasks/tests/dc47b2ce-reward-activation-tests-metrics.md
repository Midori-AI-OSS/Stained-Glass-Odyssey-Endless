# Harden reward activation with tests and monitoring

## Summary
Expand automated coverage and instrumentation to validate the guardrails added in `6ebaed1b-reward-activation-atomicity.md` and catch regressions early.

## Requirements
- Add backend tests covering double-submit attempts, reconnect flows (battle snapshot reloads), and manual `/rewards/*` retries to confirm staging guardrails hold.
- Verify that battle setup integration tests (`backend/tests/test_reward_gate.py` or equivalents) exercise the new activation pipeline and cleanup paths.
- Introduce logging or metrics counters that emit when duplicate activation attempts are blocked so live ops can detect suspicious behaviour.
- Document how to monitor these signals in `.codex/implementation/battle-endpoint-payload.md` or a dedicated ops note.

## Dependencies
Requires guardrail logic from `6ebaed1b-reward-activation-atomicity.md`.

## Out of scope
Do not modify frontend flows; focus on backend testing and observability.

## Implementation notes
- Added telemetry for blocked confirmations and extended backend/unit integration tests to cover duplicate submissions, reconnect reloads, and HTTP retries.
- Documented how to monitor the `confirm_*_blocked` events in `backend/.codex/implementation/battle-endpoint-payload.md` so ops teams know where to pull the data.
## Audit notes
- Confirmed the `/rewards/card/<run_id>/confirm` handler surfaces telemetry when a second HTTP confirmation arrives, exercising the duplicate guard in `tests/test_reward_gate.py`.【F:backend/tests/test_reward_gate.py†L360-L423】
- Verified the reconnect scenario clears the in-memory snapshot before attempting another confirmation and still records a `confirm_cards_blocked` event in `tests/test_reward_staging_confirmation.py`.【F:backend/tests/test_reward_staging_confirmation.py†L300-L338】
- Observed the backend now logs `confirm_{bucket}_blocked` events whenever the staging bucket is empty, ensuring operations can detect duplicate activations.【F:backend/services/reward_service.py†L440-L475】
- Documentation now details how to monitor the `confirm_*_blocked` telemetry, pointing operators to the `game_actions` records documented in `backend/.codex/implementation/battle-endpoint-payload.md`.【F:backend/.codex/implementation/battle-endpoint-payload.md†L147-L184】
- Re-ran the reward confirmation suites to verify the duplicate guard and reconnect flows pass under pytest. 【0e0e22†L1-L3】【1067c8†L1-L3】

requesting review from the Task Master
