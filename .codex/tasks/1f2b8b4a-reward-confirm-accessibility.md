# Finalise reward confirm accessibility & styling tokens

## Summary
Polish the shared styling and accessibility surface for the refreshed card and relic confirm controls so both phases meet keyboard, screen reader, and design expectations.

## Requirements
- Centralise stained-glass button styles, animation durations, and colour tokens in a shared stylesheet or design token file used by both card and relic confirms.
- Audit keyboard focus order through Drops → Cards → Relics to ensure tab/arrow navigation and aria attributes read correctly for confirm buttons.
- Add screen reader announcements when the confirm button appears/disappears and when selections change, following accessibility task guidance.
- Update any localisation strings or tooltip copy so both phases share the same wording.
- Provide documentation snippets or Storybook notes (if applicable) demonstrating the expected interactions for QA.

## Coordination notes
- Coordinate with the resilience task owner to avoid conflicting focus management changes.
- Loop in UX for sign-off on the shared styling tokens before merging.

## Status
- 2025-02-15: Shared confirm button tokens across card/relic phases and added live announcements for selection/confirmation state changes.
ready for review
