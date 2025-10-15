# Surface preview metadata for staged rewards to the frontend

## Summary
Design the data contracts that describe how a staged card or relic will affect the party so the UI can render previews. This includes mapping stat deltas, triggers, and any textual cues into a stable payload consumed by the frontend.

### Existing data surfaces to inspect
- `RewardOverlay.svelte` currently renders `card_choices` / `relic_choices` using only `{id, name, stars}`. It expects to receive the raw reward bundle from `battle_snapshots[run_id]` (see `.codex/implementation/post-fight-loot-screen.md`) and will need an additional, well-typed `preview` field to render staged deltas without changing the base schema.
- Card implementations inherit from `plugins.cards._base.CardBase`. Simple cards expose their multipliers via the `effects` dict (e.g. `Micro Blade` adds `{"atk": 0.03}`) while advanced cards override `apply()` to register BUS handlers. Relics follow a similar pattern under `plugins/relics/`.
- The combat engine already emits contextual signals: `DamageOverTime.tick` fires `dot_tick` events with `{ "dot_id", "remaining_turns", "original_damage" }`, `EffectManager` emits `effect_resisted`, etc. These are canonical sources for trigger previews instead of hard-coding prose.

### Implementation notes
- Define a preview schema that can represent both deterministic stat changes (`stats.max_hp.multiplier`, `stats.attack.delta`, etc.) and event-driven hooks (`triggers.on_dot_tick`, `triggers.on_effect_resisted`). Document the JSON shape in `.codex/implementation/battle-endpoint-payload.md` and mirror it in the frontend types.
- Extend the staging payload emitted by the previous task so `/ui` responses, `/rewards/cards/<run_id>`, and `/rewards/relics/<run_id>` return `{ "card": {...}, "preview": {...} }`. Make sure the snapshot stored in `battle_snapshots` contains the same structure so reconnecting clients still see previews.
- Frontend changes should live alongside the existing overlay system (`frontend/src/lib/components/RewardOverlay.svelte`, `frontend/src/lib/systems/uiApi.js`). Provide helper mappers that translate the backend schema into UI-friendly tooltip text and numerical deltas.
- Capture at least one example per reward type (flat stat buff, conditional trigger, passive-style subscription) in the documentation so plugin authors know how to populate preview metadata from their card/relic definitions.

## Deliverables
- Extend reward staging APIs to emit detailed preview metadata for each pending card or relic.
- Update the backend/frontend integration (REST or socket payloads) so clients receive the preview bundle immediately after staging, and wire the frontend overlay/components to consume it without regressing the existing reward UI.
- Provide example responses and contract documentation (including updates to `.codex/implementation/reward-overlay.md` and `.codex/implementation/battle-endpoint-payload.md`) so UI developers know how to visualize upcoming effects.

## Why this matters for players
Players want to understand what a reward does before committing. Rich preview metadata unlocks instant feedback—showing HP gains, trigger counts, or passive effects—so choices feel informed instead of blind.
