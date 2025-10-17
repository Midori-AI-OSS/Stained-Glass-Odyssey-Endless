# Rebuild reward overlay into four-phase flow

## Summary
Redesign the WebUI reward overlay so rewards resolve in four distinct phases—Drops → Cards → Relics → Battle Review—with clearer affordances that prevent the current soft-lock behaviour.

## Requirements
- Introduce explicit step sequencing in the reward overlay (Drops, Cards, Relics, Review) driven by the backend’s `reward_progression` metadata (post `a28b5711-reward-progression-consistency.md`). When the field is temporarily absent, fall back to deriving the order from `awaiting_*` flags so legacy runs continue to function.
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

## Status Assessment (2025-10-17)
### Prerequisites Completed
- ✅ `b49f64f7-card-confirmation-softlock.md` - Card soft lock fixed
- ✅ `a28b5711-reward-progression-consistency.md` - Progression metadata guaranteed
- ✅ `9dfda476-reward-confirmation-flow.md` - Confirmation flow regression fixed
- ✅ `bfb6d0b4-reward-staging-confirmation.md` - Staging confirmation finalized

### Task Scope Analysis
This is a **major frontend overhaul** requiring:
1. Complete RewardOverlay refactoring for phased flow
2. New wiggle animation system with CSS keyframes
3. Countdown timer UI component
4. Stained-glass styling integration
5. Keyboard accessibility enhancements
6. Idle-mode automation updates
7. Documentation updates

**Estimated effort:** 4-6 hours for complete implementation and testing

### Recommendation
Given the scope, this task should be:
1. Broken down into smaller sub-tasks (drops phase, card phase, relic phase, review phase)
2. Each phase implemented and tested separately
3. Integration testing after all phases complete

The prerequisite backend work is complete, so this task is **ready to start** but requires dedicated time for proper implementation.

more work needed - Prerequisites complete, ready for implementation. Task requires significant frontend work (4-6 hours estimated). Consider breaking into phases.