# Rebuild reward overlay into four-phase flow

## Status: ✅ COMPLETED

## Summary
Redesign the WebUI reward overlay so rewards resolve in four distinct phases—Drops → Cards → Relics → Battle Review—with clearer affordances that prevent the current soft-lock behaviour.

## Implementation Summary

The reward overlay now supports a four-phase flow when the backend provides `reward_progression` metadata:

1. **Drops Phase** (`current_step: 'drops'`): Shows only loot tiles with a stained-glass styled "Advance" button featuring a visible 10-second countdown. Auto-advances when timer completes, but allows early clicks. Card/relic UI hidden until drops are acknowledged.

2. **Cards Phase** (`current_step: 'cards'`): First click highlights the card and starts a subtle looping wiggle animation with randomized timing. A themed confirm button appears directly beneath the highlighted card. Second click on the same card confirms selection. Preview panel and cancel button removed in phase-based mode.

3. **Relics Phase** (`current_step: 'relics'`): Mirrors card phase behavior with highlight, wiggle animation, and on-card confirm button. Backend cancel flows clear local highlight state.

4. **Battle Review Phase** (`current_step: 'battle_review'`): Transitions to review overlay based on user settings, or auto-advances if disabled.

### Key Changes:
- Added `rewardProgression` prop to RewardOverlay component
- Implemented phase detection logic based on `current_step`
- Added wiggle animation keyframes with randomized delays (2.2s loop with subtle rotation/scale)
- Created inline confirm buttons using stained-glass styling (`--glass-bg`, `--glass-border`, `--glass-shadow`)
- Added countdown timer for drops phase with auto-advance
- Updated OverlayHost to pass `reward_progression` from roomData
- Added `advancePhase` event handler in +page.svelte that calls `advanceRoom()`
- Maintained backward compatibility: falls back to legacy behavior when `reward_progression` is not provided
- Updated documentation in `frontend/.codex/implementation/reward-overlay.md`

### Accessibility:
- Keyboard navigation fully supported
- Focus automatically moves to confirm button when it appears
- Wiggle animation respects `reducedMotion` settings
- Screen reader support maintained with proper ARIA labels

### Idle Mode:
- Automation follows new phase-based flow via `advancePhase` events
- Respects phase gates and doesn't skip unconfirmed rewards

## Requirements
- Introduce explicit step sequencing in the reward overlay (Drops, Cards, Relics, Review) driven by the backend’s `reward_progression` metadata.
- **Drops phase:** show only loot tiles (gold, damage-type items, pulls). Render a right-panel `Advance` button that matches the main-menu/party-menu style (`stained-glass` container + `icon-btn` aesthetics) and display a visible 10 s countdown beside the label. Auto-advance when the timer completes, but permit early clicks. Hide card/relic UI until drops are complete.
- **Card phase:** first click highlights the card, starts a looping wiggle animation that persists until the selection is confirmed or a different card is chosen, and reveals a themed confirm button directly beneath the selected card. Keep the wiggle subtle—small rotation/scale offsets with a hint of randomised timing so the motion feels alive but not distracting. The button should reuse the right-panel styling (same glass bar + `icon-btn` treatment). Second click on the highlighted card behaves like pressing the confirm button. Remove the existing preview panel and cancel button. Keep accessibility in mind (keyboard activation should still work and focus should move to the confirm button when it appears).
- **Relic phase:** mirror the card behaviour for relics (highlight + the same subdued, slightly randomised looping wiggle until resolved, plus on-card confirm with the same right-panel styling). Ensure cancel flows from the backend clear any local highlight state.
- **Battle review phase:** once rewards finish, transition into the review overlay only if the user setting allows it. Otherwise advance automatically.
- Refresh idle-mode automation so it follows the new step flow (engaging the confirm actions as needed) without regressing existing automation.
- Update styling and layout so the controls slot into the stained-glass side rails used by the main menu / warp / inventory: reuse shared CSS tokens (`--glass-bg`, `stained-glass-row`, `icon-btn`) or extract a dedicated helper if necessary.
- Refresh `frontend/.codex/implementation/reward-overlay.md` to document the four-step sequence, wiggle interaction, countdown advance, and removal of the preview panel.

## Dependencies & coordination
- Coordinate with the backend if additional pacing or `reward_progression` cues are needed, but avoid backend changes unless blockers arise.
- Align with any ongoing reward preview work—removing the preview panel may require updating docs/tests from those tasks.

## Out of scope
- Backend reward confirmation guardrails (already handled separately).
- New audio or haptics for the wiggle animation.

## Notes
- Wiggle animation does not exist yet; define new CSS keyframes/utility classes in the card/relic components.
- Make sure keyboard users can highlight and confirm without relying on pointer hover.
