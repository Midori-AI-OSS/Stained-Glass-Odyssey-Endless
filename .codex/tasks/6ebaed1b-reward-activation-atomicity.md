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

### Documentation refresh (2025-02-20)
- Added a "Single-confirm guardrails" section to `.codex/implementation/post-fight-loot-screen.md` describing the per-run mutex, staging cleanup, activation log, and `advance_room` gate.
- Documented the `reward_activation_log` payload in `.codex/implementation/save-system.md` so the persistent schema notes cover the audit breadcrumbs.
- Expanded `.codex/implementation/reward-overlay.md` with the confirmation response contract, including activation records and mutex-driven duplicate protection for reconnects.

### Auditor confirmation (2025-02-20)
- Verified `services.reward_service.confirm_reward` enforces the per-run `reward_locks` mutex, clears staging buckets, updates the `awaiting_*` flags, and appends bounded activation records mirrored into battle snapshots.【F:backend/services/reward_service.py†L399-L507】
- Confirmed both `/ui` and service-level room advancement guards call `has_pending_rewards` so pending staging data blocks map progression until all rewards are resolved.【F:backend/routes/ui.py†L480-L521】【F:backend/services/run_service.py†L500-L537】【F:backend/runs/lifecycle.py†L452-L469】
- Checked the refreshed implementation docs describe the mutex, activation log payload, and confirmation response contract that now surface on the API.【F:.codex/implementation/post-fight-loot-screen.md†L12-L26】【F:.codex/implementation/save-system.md†L9-L20】【F:.codex/implementation/reward-overlay.md†L17-L36】
- Re-ran `uv run pytest tests/test_reward_staging_confirmation.py tests/test_reward_gate.py` to exercise the single-confirm guardrails and the advancement gate (all passing).【36ec08†L1-L2】【f63c5e†L1-L4】

requesting review from the Task Master
