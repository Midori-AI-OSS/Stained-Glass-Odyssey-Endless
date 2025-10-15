# Guarantee single activation and solid tests for reward staging

## Summary
Once a player accepts a staged reward, we need deterministic activation and guardrails that prevent duplicate applications or lingering staged entries. This task covers the confirmation pipeline, cleanup, and regression tests around both battle setup and backtracking scenarios.

## Deliverables
- Update reward activation logic so staged entries are applied exactly once and cleared afterward, even across reconnects or retries.
- Add automated tests covering double-accept attempts, battle setup integration, and cancellation flows.
- Instrument logging or metrics to flag unexpected duplicate activations for live ops follow-up.

## Why this matters for players
Without strong guardrails, players risk losing rewards or gaining unintended double buffs when staging is introduced. Reliable activation keeps progression fair and predictable, maintaining trust in the reward system.
