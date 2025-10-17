# Fix card confirmation soft lock loop

## Summary
Audit **f6409b29** found that confirming the first post-battle card reward immediately snaps the UI back to the selection state instead of advancing to the next reward. Players become permanently stuck on the reward screen and cannot progress past room 2.

## Impact
- Blocks 100% of runs after the very first battle, rendering the game unplayable beyond room 2.
- QA cannot execute playtests or audits past the initial reward phase.
- Any downstream systems that rely on progressing past the first reward (shops, relics, map events) are completely untested.

## Reproduction
1. Start a new run in the current frontend build.
2. Clear the first (weak) battle.
3. Select any card reward and click **Confirm**.
4. Observe the overlay return to the card selection screen instead of advancing to relic/loot review.

## Expected behavior
- Confirming a card should consume the staged reward, update the run state, and advance the overlay to the next reward step (relic, loot review, or map advance) without reopening the selection list.

## Required work
### Frontend
- Trace the confirmation flow (`RewardOverlay.svelte → handleConfirm('card') → uiApi.sendAction('confirm_card')`) to ensure the state update from the backend clears the card selection mode and transitions the overlay to the next reward step.
- Inspect `applyRewardPayload` (or the equivalent state sync helper) and any derived stores to confirm `awaiting_card` flips to `false` and `reward_progression`/`reward_staging` are respected after confirmation.
- Add defensive handling so duplicate `confirm_card` responses or mismatched progression payloads cannot reopen the card selection step.
- Reinstate or add console logs/telemetry around confirm → next-phase transitions to aid future audits, as recommended in audit f6409b29.

### Backend (verification)
- Double-check the `/ui?action=confirm_card` response includes the fields the frontend expects (`reward_progression`, `awaiting_*`, `reward_staging`, updated party data). Confirm no regression in `reward_service.confirm_reward` that could re-flag `awaiting_card`.

## Testing
- Manual: reproduce the audit steps and verify the overlay advances past the card reward and the run proceeds to room 3.
- Automated: extend existing frontend integration/unit coverage to assert that confirming a staged card transitions `awaiting_card` to `false` and triggers the next step. If feasible, add a regression test around the state machine that previously caused the loop.

## References
- `.codex/audit/f6409b29-game-playtest-audit.audit.md`
- Frontend: `frontend/src/routes/(app)/game/+page.svelte`, `frontend/src/lib/overlays/RewardOverlay.svelte`, `frontend/src/lib/systems/uiApi.js`
- Backend: `backend/routes/ui.py`, `backend/services/reward_service.py`

ready for review
