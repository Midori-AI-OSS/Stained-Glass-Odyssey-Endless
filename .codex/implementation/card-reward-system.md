# Card Reward System

Battles grant unique cards that permanently boost party stats. Cards come in star ranks and only one copy of each can be owned. Victories present three unused cards of the appropriate star rank; choosing one adds it to the party's inventory. Cards are implemented as plugins under `plugins/cards/`, making new rewards easy to add. Card and relic bonuses now apply at the start of each combat rather than on acquisition so higher-star effects trigger correctly. Subsequent battles skip duplicates by rolling only from cards not yet collected.【F:backend/services/reward_service.py†L68-L205】【F:backend/plugins/cards/_base.py†L20-L120】

## Reward staging and progression

Selecting a card calls `services.reward_service.select_card`, which validates the choice against `card_choice_options`, instantiates the plugin, and stages a preview payload under `reward_staging['cards']`. The backend records `awaiting_card = True`, clears `awaiting_next`, and advances the four-phase `reward_progression` state machine so reconnecting clients know Cards is the active phase.【F:backend/services/reward_service.py†L68-L205】【F:backend/runs/lifecycle.py†L140-L220】

Confirming the staged card appends it to the party, emits an `activation_record` (with timestamp and activation ID), and adds the entry to the bounded `reward_activation_log`. Once confirmations clear all staging buckets the backend flips `awaiting_next = True`, allowing `/ui?action=advance_room` to progress the run.【F:backend/services/reward_service.py†L490-L574】 Cancelling a staged card sets `awaiting_card = True`, reopens the phase in `reward_progression`, and leaves `reward_staging['cards']` empty so the player can pick again.【F:backend/services/reward_service.py†L541-L608】

## Plugin authoring guidelines

Card plugins subclass `CardBase` and should populate:

- `effects`: base stat modifiers used by `build_preview_from_effects` to derive preview deltas.
- `preview_summary`, `preview_triggers`, or `build_preview`: optional hooks for custom copy, trigger descriptions, or stack-aware summaries. Returning a dict from `build_preview` allows cards to expose multi-target stats or custom triggers while `merge_preview_payload` backfills missing fields for reconnect stability.【F:backend/plugins/cards/_base.py†L130-L190】【F:backend/autofighter/reward_preview.py†L55-L189】
- `about`: the inventory tooltip shown when the card is staged or owned. Keep this text accurate so reconnects and doc views stay in sync.

Cards that grant conditional effects (e.g., Balance tokens each round) should describe the trigger via `preview_triggers` so the overlay lists the event and narration. If the card stacks with existing bonuses, include stack maths in the preview payload to surface `previous_total` and `total_amount` fields for the UI formatter.【F:frontend/src/lib/utils/rewardPreviewFormatter.js†L1-L200】

## Telemetry and QA notes

Each selection emits `log_game_action("select_card", …)` with the staged payload, while confirmations log `confirm_card` alongside the generated activation ID. QA can verify the overlay’s phase rail and countdown match the backend `reward_progression` snapshot and that cancelling a staged card re-enables the confirm panel. Automation helpers pause while `awaiting_card` is true and resume once `reward_staging['cards']` is empty.【F:backend/services/reward_service.py†L122-L205】【F:frontend/tests/reward-overlay-confirmation-flow.vitest.js†L21-L205】【F:frontend/tests/reward-automation.vitest.js†L40-L80】

## Testing
- `uv run pytest backend/tests/test_card_rewards.py`
- `uv run pytest backend/tests/test_reward_staging_confirmation.py`
- `bun test frontend/tests/reward-overlay-confirmation-flow.vitest.js`
