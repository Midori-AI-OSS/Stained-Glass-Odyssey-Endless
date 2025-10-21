# Implement reward card highlight & wiggle behaviour

## Summary
Rework the reward card phase so the selected card visually stands out with a looping wiggle animation and exposes an on-card confirm action.

## Requirements
- When entering the Card phase, auto-select the first card and render an on-card confirm button below it using the stained-glass button style.
- Create a subtle wiggle animation (rotation + scale jitter) applied only to the highlighted card; ensure it pauses when the card loses focus/selection.
- Support both mouse/touch re-selection and keyboard navigation; second click or confirm button should dispatch the card confirm event.
- Ensure animation tokens/config values live in a shared location so relic tasks can reuse them.
- Add component-level tests to verify selection defaults, confirm button rendering, and animation class toggling.

## Coordination notes
- Hand off the animation token details to the relic task owner for parity.
- Confirm the confirm event name/signature with backend or automation maintainers so hooks remain consistent.

ready for review
