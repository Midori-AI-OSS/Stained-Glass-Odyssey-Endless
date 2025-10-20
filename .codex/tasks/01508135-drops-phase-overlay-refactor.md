# Build drops-only reward phase experience

## Summary
Implement the UI pieces for the Drops phase so loot tiles render in isolation and subsequent reward controls remain hidden until the controller advances.

## Requirements
- Subscribe to the new reward overlay state machine and render the Drops grid when `currentPhase === "drops"`.
- Gate all card, relic, and review components (including confirm buttons) behind later phases so they are not present in the DOM during Drops.
- Ensure the right-rail shows a phase indicator/progress breadcrumbs but hides action buttons until the advance countdown task lands.
- Provide analytics/telemetry hook (if existing system) noting when the Drops phase completes so automation can confirm the transition.
- Validate layout responsiveness on mobile/tablet breakpoints so the isolated Drops screen still fits within the overlay constraints.

## Coordination notes
- Pair with the advance button implementer to confirm how the controller signals Drops completion.
- Flag any styling tokens needed for shared stained-glass visuals so the follow-up task can reuse them.
ready for review
