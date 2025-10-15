# Define reward preview metadata schema on the backend

## Summary
Translate staged reward effects into a structured preview payload that captures stat deltas and trigger hooks before frontend integration begins.

## Requirements
- Audit card and relic plugin interfaces (`plugins/cards/_base.py`, `plugins/relics/`) to catalogue the effect data available for previews.
- Design a typed schema (Python dataclasses or typed dict) that can represent flat stat changes, percentage modifiers, and trigger subscriptions (e.g., `on_dot_tick`).
- Extend staging payloads (`/ui`, `/rewards/cards`, `/rewards/relics`, battle snapshots) to include `{ "preview": ... }` alongside the existing reward metadata.
- Provide representative fixture examples in `.codex/implementation/battle-endpoint-payload.md` so downstream clients know how to interpret the schema.

## Dependencies
Requires staging infrastructure from `431efb19-reward-staging-schema.md` and `e69ad95e-reward-staging-service-hooks.md`.

## Out of scope
Do not touch frontend components yet—that work happens in a separate task.
