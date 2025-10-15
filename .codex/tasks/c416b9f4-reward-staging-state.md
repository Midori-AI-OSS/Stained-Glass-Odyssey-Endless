# Build a reward staging state separate from the active deck

## Summary
Establish a dedicated staging container for newly awarded cards and relics so their modifiers are queued rather than applied immediately. The state should persist alongside the party record and expose lifecycle hooks for when a player previews, confirms, or cancels a reward.

## Deliverables
- Schema or data structure additions that persist pending rewards independently of the active card/relic pools.
- Service-level APIs (or updates to `reward_service`) that enqueue rewards into the staging state and surface their pending status to callers.
- Clear lifecycle handling covering preview start, confirmation, and cancellation, including persistence tests.

## Why this matters for players
Players currently receive no feedback at pick time because modifiers only land during the next battle setup. Staging the rewards unlocks immediate previews while keeping the actual party deck untouched until they commit, eliminating surprise stat swings between fights.
