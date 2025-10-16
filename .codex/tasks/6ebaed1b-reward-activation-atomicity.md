# Enforce single-use activation of staged rewards

## Summary
Implement guardrails that ensure a staged reward can be confirmed only once, even across reconnects or repeated API calls.

## Requirements
- Update confirmation logic to atomically move staged rewards into the party and clear staging entries, protecting against double-submits and race conditions.
- Adjust `advance_room` (and any callers that transition the map) so it verifies both `awaiting_*` flags and the staging buckets are empty before progressing.
- Persist and surface audit-friendly markers (e.g., activation timestamps or ids) to support debugging unexpected duplicate activations.
- Refresh backend documentation describing the confirmation pipeline to highlight the new guardrails.

## Dependencies
Complete staging schema/service/confirmation tasks (`431efb19`, `e69ad95e`, `bfb6d0b4`) first.

## Out of scope
Extended test coverage and metrics instrumentation live in the companion task `tests/dc47b2ce-reward-activation-tests-metrics.md`.

### Audit notes (2025-10-16)
- Confirmed `backend/services/reward_service.py` now serialises confirmations under `reward_locks`, clears staging buckets, and appends activation records with bounded history.
- Verified both `backend/routes/ui.py` and `backend/services/run_service.py` gate `advance_room` on empty staging via `has_pending_rewards` and refreshed docs in `.codex/implementation` describe the guardrails.
- Exercised the new pytest coverage: `tests/test_reward_staging_confirmation.py` and `tests/test_reward_gate.py`.

requesting review from the Task Master
