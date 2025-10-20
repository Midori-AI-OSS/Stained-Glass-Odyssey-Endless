# Refresh reward card & relic confirmation UX

## Summary
Umbrella pointer for the card/relic interaction refresh. The work is now split so animation, relic parity, and accessibility/styling polish can proceed in parallel.

## Subtasks
- `.codex/tasks/ebfb0389-card-highlight-wiggle.md` — implement the card highlight, wiggle, and confirm control.
- `.codex/tasks/d7196ce9-relic-highlight-confirm.md` — apply the same interaction model to relics and handle reset events.
- `.codex/tasks/1f2b8b4a-reward-confirm-accessibility.md` — centralise styling tokens and finalise accessibility hooks.

## Notes
- Coordinate timelines with the phase controller subtasks so confirm hooks wire into the shared state machine cleanly.
- Update this parent as subtasks close or if additional polish work is identified.
