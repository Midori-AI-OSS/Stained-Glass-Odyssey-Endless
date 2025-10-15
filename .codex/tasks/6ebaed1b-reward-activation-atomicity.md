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
