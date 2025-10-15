# Surface preview metadata for staged rewards to the frontend

## Summary
Design the data contracts that describe how a staged card or relic will affect the party so the UI can render previews. This includes mapping stat deltas, triggers, and any textual cues into a stable payload consumed by the frontend.

## Deliverables
- Extend reward staging APIs to emit detailed preview metadata for each pending card or relic.
- Update the backend/frontend integration (REST or socket payloads) so clients receive the preview bundle immediately after staging.
- Provide example responses and contract documentation so UI developers know how to visualize upcoming effects.

## Why this matters for players
Players want to understand what a reward does before committing. Rich preview metadata unlocks instant feedback—showing HP gains, trigger counts, or passive effects—so choices feel informed instead of blind.
