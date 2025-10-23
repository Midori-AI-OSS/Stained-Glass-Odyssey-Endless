# Refresh reward flow docs for staging and previews

## Summary
Document the new staged reward pipeline so plugin authors, designers, and QA understand how to supply preview data and when effects finalize. Capture state diagrams, API hooks, and best practices in the relevant `.codex/instructions/` and implementation notes.

### Documentation targets
- `.codex/implementation/post-fight-loot-screen.md` and `.codex/implementation/battle-endpoint-payload.md` describe the payload emitted by `_run_battle`/`battle_snapshots`; they need updated field tables for `reward_staging`, preview metadata, and the acceptance workflow.
- `.codex/implementation/reward-overlay.md` plus the related UI docs (`frontend` overlay components) must be expanded so frontend contributors know where preview text, stat deltas, and confirmation prompts appear.
- `.codex/implementation/card-reward-system.md`, `.codex/implementation/relic-picker.md`, and the plugin author guides should explain how cards/relics surface preview metadata (e.g., mapping `CardBase.effects` and BUS triggers into the new schema).
- Add a concise state-machine diagram (staged → previewed → confirmed → applied) covering both happy path and cancellation/retry loops, with notes about how `reward_progression` and `awaiting_*` flags map to UI states.

### Implementation notes
- Document the API contract for `/rewards/cards/<run_id>`, `/rewards/relics/<run_id>`, `/rewards/loot/<run_id>`, and `/ui` so QA can diff payloads before/after staging.
- Provide QA checklists that cover reconnect/resume scenarios (battle snapshots, `/ui` polling) and regression checks for `advance_room` guardrails.
- Include cross-links to any new telemetry/logging fields introduced by the guardrail task so live ops can trace reward activation anomalies.

## Deliverables
- Update backend reward service documentation to describe staging, preview metadata, and confirmation steps.
- Add guidance for card/relic plugin authors on declaring preview output and activation hooks (update `.codex/instructions/` guidance plus plugin reference docs).
- Provide QA checklists covering preview display, confirmation, rollback/retry behaviors, and reconnect flows (document expected REST payloads and UI transitions).

## Why this matters for players
Clear documentation speeds up adoption of the staging system, meaning more rewards arrive with accurate previews and fewer bugs. Faster iteration keeps the game feeling polished and responsive to player feedback.
