# Ship reward overlay advance button & countdown

## Summary
Add the stained-glass right-rail with a manual `Advance` button, integrate a 10-second countdown timer, and wire both into the reward overlay controller.

## Requirements
- Render the right-rail panel with stained-glass styling, including phase labels and an `Advance` button that uses shared button tokens.
- Implement a countdown timer that starts when a phase becomes completable, displays remaining seconds, and auto-triggers the advance handler when it reaches zero.
- Allow manual button clicks to advance immediately, cancelling the countdown when pressed.
- Ensure the timer pauses or resets correctly when phases are skipped by the controller (e.g., backend indicates no relics).
- Cover edge cases such as multiple rapid clicks, countdown jitter, and overlay unmounts with unit/component tests.

## Coordination notes
- Confirm animation/styling expectations with the UX owner before finalising CSS variables.
- Provide an event or callback the automation task can hook into for validating auto-advance in tests.
ready for review
