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
