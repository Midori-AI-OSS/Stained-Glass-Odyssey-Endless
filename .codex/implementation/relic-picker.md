# Relic Picker Flow

When a battle ends, the backend rolls for a relic drop. Normal fights grant a relic 10% of the time, while boss rooms roll at 50%. If a relic is awarded, its star rank is determined by the encounter type and three relic options of that rank are returned to the frontend.【F:backend/services/reward_service.py†L206-L324】

The frontend displays these options in the reward overlay using the same star-color tinting as cards. Selecting a relic posts the choice to `/relics/<run_id>`; the backend saves the relic to the run and only allows advancing rooms once all reward selections are complete.【F:frontend/src/lib/components/RewardOverlay.svelte†L1-L220】【F:backend/services/reward_service.py†L206-L417】

## Reward staging and confirmation

`select_relic` instantiates the relic plugin, measures existing stacks on the party, and stages the preview payload under `reward_staging['relics']`. The backend marks `awaiting_relic = True`, clears `awaiting_next`, and advances `reward_progression` so reconnects and automation know the Relics phase is active.【F:backend/services/reward_service.py†L206-L324】【F:backend/runs/lifecycle.py†L140-L220】 The staged payload includes the next-stack preview so the overlay can show the exact stats and triggers that will apply if the relic is confirmed.【F:backend/services/reward_service.py†L206-L324】【F:backend/autofighter/reward_preview.py†L55-L189】

Confirming a relic appends it to the party inventory, pushes an activation snapshot into `reward_activation_log`, and advances the progression sequence. Cancelling clears the staging bucket, reopens the relic phase, and keeps `awaiting_relic = True` until a new choice is staged.【F:backend/services/reward_service.py†L490-L608】

## Plugin authoring guidelines

Relic plugins mirror the card workflow:

- Define `effects` for flat or percentage stat bonuses.
- Override `build_preview` when stacks or bus subscriptions need bespoke copy, calling `merge_preview_payload` to merge custom fields with default stat math.【F:backend/plugins/relics/_base.py†L70-L150】【F:backend/autofighter/reward_preview.py†L55-L189】
- Populate `about` with accurate next-stack text so preview summaries stay trustworthy.

Use `preview_triggers` or a custom payload to document event hooks (`on_battle_start`, `on_turn_end`, etc.) so the overlay communicates reactive behaviour. If a relic unlocks abilities when stacked, include the projected totals in the preview stats so QA can validate the math during the confirmation flow.【F:frontend/src/lib/utils/rewardPreviewFormatter.js†L1-L200】

## Telemetry and QA notes

`select_relic` logs `log_game_action("select_relic", …)` with the staged payload, while confirmations emit `confirm_relic` alongside the activation ID. QA should confirm that cancelling returns the phase rail to Relics, that `awaiting_relic` toggles appropriately, and that automation only advances once staging is clear.【F:backend/services/reward_service.py†L244-L341】【F:frontend/tests/reward-overlay-confirmation-flow.vitest.js†L134-L213】【F:frontend/tests/reward-automation.vitest.js†L70-L110】

## Testing
- `uv run pytest backend/tests/test_relic_rewards.py`
- `uv run pytest backend/tests/test_reward_staging_confirmation.py`
- `bun test frontend/tests/reward-overlay-confirmation-flow.vitest.js`
