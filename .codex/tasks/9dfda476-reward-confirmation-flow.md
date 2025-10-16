# Fix reward confirmation flow regression

## Summary
Players who pick a card or relic after battle receive an error — "Cannot advance room until all rewards are collected" — even though the reward overlay no longer shows any choices. The regression started after the backend introduced staged rewards that must be confirmed before the room can advance.

## Impact
- Runs become stuck after any encounter that grants a card or relic; players cannot progress without using the hidden "Force Next Room" debug control.
- Daily streaks, shop access, and run persistence all break for affected players because the run never reaches the next room.
- QA cannot verify new reward content because confirmations never fire.

## Current behavior
1. Player clears a battle and the reward overlay offers a card or relic.
2. Clicking a reward calls `/ui?action=choose_card|choose_relic`, which now stages the selection and marks `awaiting_card` or `awaiting_relic` as `True` in `runs.lifecycle`.
3. The frontend immediately hides the choice but never calls the new confirmation endpoints (`/ui?action=confirm_card|confirm_relic`).
4. `advance_room` rejects the request while any `awaiting_*` flag remains set, so the UI shows the blocking error toast and the run soft-locks.

The overlay never renders staged rewards from `reward_staging`, so the player cannot review or confirm their pick.

## Expected behavior
- After staging a reward, the overlay should surface the staged entry, expose **Confirm** and **Cancel** controls, and call the appropriate backend endpoint.
- Confirming must clear the staging bucket, propagate the updated party loadout, and unblock `advance_room` once no other rewards remain.
- Canceling should restore the choice list so players can pick again.

## Proposed work
### Frontend
- Extend `GameViewport`/`OverlayHost` plumbing so `RewardOverlay` receives staged rewards (`roomData.reward_staging`) alongside `awaiting_*` flags.
- Update `RewardOverlay` to show staged cards/relics with preview text and render explicit **Confirm** and **Cancel** actions that dispatch new events.
- Add UI API helpers for `confirm_card`, `confirm_relic`, `cancel_card`, and `cancel_relic` that call the existing `/ui` actions. Ensure responses update `runState` and cached map data (`reward_staging`, `awaiting_*`, `next_room`).
- Adjust `handleRewardSelect` and idle-mode automation to call the confirm helpers instead of advancing directly. Make sure the overlay stays mounted until the confirmation succeeds.
- Refresh reward polling/auto-advance logic so rooms advance automatically when `awaiting_next` flips to `true` and no battle review is pending.
- Update `.codex/implementation/reward-overlay.md` to describe the confirm/cancel UI flow.

### Backend (follow-up verification)
- Double-check that `/ui?action=confirm_*` responses include the staged reward summary, updated party lists, `awaiting_*` flags, and `next_room` hints so the frontend can sync without an immediate map refresh.
- Add regression tests, if missing, that cover staging → confirm → advance for both cards and relics.

## Dependencies & coordination
- Coordinate with any ongoing reward preview tasks (`f2622706-reward-preview-frontend.md`, `b30ad6a1-reward-preview-schema.md`) so the confirm UI meshes with forthcoming preview metadata.

## Testing guidance
- Manual: clear a battle, stage a card, confirm it, and verify `advance_room` succeeds and the deck updates.
- Automated: add frontend integration/unit tests for the confirm handlers if feasible; backend pytest coverage for staged confirmation sequences.

