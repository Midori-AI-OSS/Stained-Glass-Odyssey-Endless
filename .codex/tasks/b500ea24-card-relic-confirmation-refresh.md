# Refresh reward card & relic confirmation UX

## Summary
Update the reward overlay's card and relic selection experience with accessible highlight, wiggle, and confirm behaviours that match the stained-glass control styling.

## Requirements
- When entering the Card phase, highlight the first selected card and apply a subtle looping wiggle animation (small rotation + scale jitter with a touch of randomness) that persists until confirmation or a different card is chosen.
- Replace the existing preview panel with an on-card confirm button that mirrors the stained-glass right-rail styling and appears directly beneath the highlighted card; second clicks on the highlighted card should trigger the same confirm.
- Mirror the same highlight + wiggle + confirm flow for relic selection, including clearing any highlight when backend cancel/reset events occur.
- Preserve keyboard accessibility: focus should move to the confirm control when it appears, Enter/Space should confirm, and arrow/tab navigation should allow changing the selection.
- Remove the old cancel button, ensuring there is a clear keyboard path to back out if the backend exposes a cancel action.
- Ensure styling tokens (`--glass-bg`, `stained-glass-row`, `icon-btn`) are reused or centralised to keep consistency with other overlays.

## Coordination notes
- Collaborate with whoever owns idle automation to align on new confirm hooks before merging.
- Sync with any concurrent reward preview work so documentation/tests are updated consistently.
