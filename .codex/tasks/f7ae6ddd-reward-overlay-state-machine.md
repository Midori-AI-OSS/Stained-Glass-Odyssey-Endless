# Implement reward overlay state machine scaffold

## Summary
Define the frontend reward overlay controller that ingests `reward_progression` from the backend and exposes a deterministic phase state machine for Drops → Cards → Relics → Battle Review.

## Requirements
- Parse `reward_progression` payloads in the overlay store/component and normalise them into a typed sequence of phases.
- Represent the flow as an explicit finite state machine (or equivalent enum + reducer) that exposes current phase, next phase, and helper methods for advancing and skipping.
- Guarantee the state machine tolerates missing or reordered phases by falling back to a safe default order while logging diagnostics for QA.
- Emit events/hooks the rest of the overlay can subscribe to for phase entry/exit so follow-up UI tasks can attach behaviour without reimplementing the progression logic.
- Provide unit coverage over the reducer/state helper to lock in transitions, skip handling, and invalid metadata fallbacks.

## Coordination notes
- Align with backend maintainers on expected `reward_progression` schema shape before hard-coding assumptions.
- Hand off the exposed hooks to the UI implementers working on Drops/Confirm tasks so they can rely on the same API.
