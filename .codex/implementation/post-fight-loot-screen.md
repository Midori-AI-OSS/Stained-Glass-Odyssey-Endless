# Post-Fight Loot Screen

After a battle concludes the frontend polls `roomAction(runId, 'battle', 'snapshot')` until the snapshot includes a `loot` object summarizing gold earned and any reward choices. `OverlayHost.svelte` keeps `BattleView.svelte` mounted during this polling and only opens `RewardOverlay.svelte` once the `loot` data arrives and combat is flagged complete. Players must resolve the four reward phases—Drops, Cards, Relics, and optional Battle Review—before pressing **Next Room** to call `/run/<id>/next` and advance the run.【F:frontend/src/lib/components/OverlayHost.svelte†L1-L220】【F:frontend/src/lib/systems/rewardProgression.js†L1-L260】

## Reward staging persistence
- The run map JSON stored in `runs.map` now includes a `reward_staging` object with `cards`, `relics`, and `items` arrays. These buckets capture unconfirmed selections so reconnecting clients can resume the overlay without mutating the live party loadout. Each staged entry embeds a normalised `preview` payload so the UI can narrate the pending stats and trigger hooks before confirmation.【F:backend/services/reward_service.py†L42-L205】
- `runs.lifecycle.load_map` backfills `reward_staging` and the new `reward_progression` field for older saves, mirroring the data into any in-memory battle snapshot (`battle_snapshots[run_id]`) so `/ui` and `/map/<id>` consumers receive the same staged entries and phase metadata.【F:backend/runs/lifecycle.py†L140-L266】
- `runs.lifecycle.save_map` always normalises `reward_staging` and recomputes `reward_progression` before writing so downstream services can append staged rewards without defensive guards. Confirmation clears the buckets while cancellation reopens the matching phase and restores the appropriate `awaiting_*` flags.【F:backend/services/reward_service.py†L324-L417】【F:backend/services/reward_service.py†L490-L608】
- Every confirmation appends an `activation_record` to `reward_activation_log`. Snapshots mirror this bounded log and the latest `reward_progression` payload, giving reconnects and QA an audit trail of staged payloads, completion timestamps, and generated activation IDs.【F:backend/services/reward_service.py†L520-L574】

## Single-confirm guardrails
- `services.reward_service.confirm_reward` acquires a per-run `reward_locks[run_id]` mutex before mutating staging data, ensuring duplicate HTTP calls or reconnects cannot race each other while a confirmation is in flight.【F:backend/services/reward_service.py†L520-L574】
- On success the targeted staging bucket is cleared, the appropriate `awaiting_*` flags are flipped off, and `awaiting_next` is only raised once every bucket is empty. Failed or replayed confirmations raise an error because the staging list is empty.【F:backend/services/reward_service.py†L490-L574】
- Each activation appends a record to `state["reward_activation_log"]` with a generated `activation_id`, timestamp, bucket name, and the committed payload. Snapshots mirror this log so the frontend can surface audit breadcrumbs and the backend retains the last 20 activations for debugging.【F:backend/services/reward_service.py†L520-L574】
- `services.run_service.advance_room` now blocks when any staging bucket still contains entries via `runs.lifecycle.has_pending_rewards`, preventing map progression until the overlay has been fully resolved.【F:backend/routes/ui.py†L495-L695】

## Reward progression state machine

The backend exposes a canonical Drops → Cards → Relics → Battle Review sequence through `reward_progression`. The frontend ingests this payload with `rewardPhaseController` to drive the overlay rail, countdowns, and automation fallbacks.【F:backend/runs/lifecycle.py†L140-L220】【F:frontend/src/lib/systems/rewardProgression.js†L1-L260】 The states surface through `awaiting_*` flags and map directly to UI affordances:

```text
Drops (awaiting_loot = True, reward_progression.current_step = 'drops')
    │ acknowledge_loot / auto-advance
    ▼
Previewed card (reward_staging['cards'] populated, awaiting_card = True)
    │  ┌─ cancel_card → reopen step (awaiting_card = True)
    │  │
    │  └─ confirm_card → activation log entry, awaiting_card = False
    ▼
Previewed relic (reward_staging['relics'] populated, awaiting_relic = True)
    │  ┌─ cancel_relic → reopen step (awaiting_relic = True)
    │  │
    │  └─ confirm_relic → activation log entry, awaiting_relic = False
    ▼
Battle Review (reward_progression.current_step = 'battle_review')
    │ auto-completes when countdown fires or automation advances
    ▼
Applied (awaiting_next = True) → `/run/<id>/next`
```

The UI announces each phase transition, activates the confirm panel when staging entries exist, and returns to Drops if cancellation reopens a bucket. When `reward_progression` is missing or malformed the overlay falls back to legacy behaviour and surfaces a warning banner for QA.【F:frontend/src/lib/components/RewardOverlay.svelte†L1-L220】【F:frontend/src/lib/components/RewardOverlay.svelte†L600-L760】

## API contracts

### `POST /rewards/cards/<run_id>`
- **Body**: `{ "card": "<card_id>" }`
- **Response**: staged card payload with preview metadata, `reward_staging`, updated `awaiting_*` flags, next room hint, and the current `reward_progression` snapshot. The handler rejects invalid IDs, duplicate ownership, or stale selections so only fresh options can be staged.【F:backend/services/reward_service.py†L68-L205】
- **Side effects**: persists map state, copies staging into live snapshots, and emits `log_game_action("select_card", …)` telemetry with the staged payload for audit correlation.【F:backend/services/reward_service.py†L122-L171】

### `POST /rewards/relics/<run_id>`
- **Body**: `{ "relic": "<relic_id>" }`
- **Response**: mirrors the card endpoint but with relic metadata. Existing stacks are counted so previews reflect the next stack, and the `reward_progression` sequence advances to the relic phase.【F:backend/services/reward_service.py†L206-L324】
- **Side effects**: persists state, refreshes snapshots, and emits `log_game_action("select_relic", …)` with staging details.【F:backend/services/reward_service.py†L244-L318】

### `POST /rewards/loot/<run_id>`
- **Body**: none required.
- **Response**: returns `{ "next_room": <type|null> }`. When loot was already cleared the response includes the next room while logging an idempotent acknowledgement. Otherwise the call clears item staging, advances Drops in `reward_progression`, and rewrites snapshots before returning the next room type.【F:backend/services/reward_service.py†L288-L341】
- **Side effects**: writes to the run map, updates `awaiting_*` flags, and emits `log_game_action("acknowledge_loot", …)` with an `idempotent` hint so telemetry distinguishes replays.【F:backend/services/reward_service.py†L300-L341】

### `POST /ui`
- **`action="choose_card" | "choose_relic"`**: thin wrappers around the staging endpoints that forward the response payload directly to the client.【F:backend/routes/ui.py†L702-L752】
- **`action="confirm_card" | "confirm_relic"`**: call `confirm_reward`, returning the updated staging payload, `activation_record`, and refreshed `reward_progression`. Duplicate confirmations raise `400` with an error message, and telemetry is emitted as `confirm_card` / `confirm_relic`.【F:backend/routes/ui.py†L740-L770】【F:backend/services/reward_service.py†L520-L574】
- **`action="cancel_card" | "cancel_relic"`**: clear staged entries, reopen the relevant phase, and return updated `awaiting_*` flags. QA should see `awaiting_next` drop back to `False` until a new selection is staged.【F:backend/routes/ui.py†L766-L785】【F:backend/services/reward_service.py†L541-L608】
- **`action="advance_room"`**: verifies all reward phases are complete. If a bucket is still pending it returns a `pending_rewards` payload describing the blocking phase, current `reward_progression`, and any outstanding choices; otherwise it completes remaining phases (including auto-completing Battle Review) before calling `advance_room`. This call ensures the run cannot progress while staging entries exist.【F:backend/routes/ui.py†L495-L695】

## Telemetry and audit trail

Reward interactions stream structured telemetry through `log_game_action` with unique events for selection, confirmation, cancellation, and loot acknowledgement. Each event includes the run ID, room identifier, and contextual details such as the staged payload, activation ID, `next_room`, or failure reason so Live Ops can trace regressions back to player actions.【F:backend/services/reward_service.py†L120-L341】【F:backend/services/reward_service.py†L520-L574】

## QA checklist

- Verify Drops → Cards → Relics → Battle Review ordering using the phase rail and ensure `reward_progression.current_step` mirrors the visible phase after each action.【F:frontend/src/lib/components/RewardOverlay.svelte†L1-L220】【F:frontend/tests/reward-overlay-confirmation-flow.vitest.js†L21-L133】
- Stage a card, cancel it, and confirm a different option. Observe that `awaiting_card` toggles back to `True` on cancel and that the confirmation response appends to `reward_activation_log`.【F:backend/services/reward_service.py†L490-L574】【F:frontend/tests/reward-overlay-confirmation-flow.vitest.js†L66-L205】
- Confirm that loot acknowledgement advances Drops and unblocks Cards without leaving stray staged items. Check `/ui?action=advance_room` returns `pending_rewards` until all buckets clear.【F:backend/services/reward_service.py†L288-L341】【F:backend/routes/ui.py†L495-L695】
- Reconnect mid-flow and ensure the overlay restores staged previews, countdowns, and `awaiting_*` flags from the snapshot payload. Fallback warnings should only appear when `reward_progression` is absent or malformed.【F:backend/services/reward_service.py†L324-L417】【F:frontend/src/lib/components/RewardOverlay.svelte†L600-L760】
- Run automation helpers in idle mode and confirm they continue to auto-select choices and advance phases when staging is empty.【F:frontend/src/lib/utils/rewardAutomation.js†L1-L200】【F:frontend/tests/reward-automation.vitest.js†L1-L120】

## Testing
- `uv run pytest backend/tests/test_loot_summary.py`
- `uv run pytest backend/tests/test_reward_staging_confirmation.py`
- `uv run pytest backend/tests/test_reward_gate.py`
- `bun test frontend/tests/reward-overlay-confirmation-flow.vitest.js`
- `bun test frontend/tests/reward-automation.vitest.js`
