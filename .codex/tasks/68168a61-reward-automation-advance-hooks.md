# Update idle automation for four-phase rewards

## Summary
Teach the idle automation/assist scripts to drive the new Drops → Cards → Relics → Review flow, invoking the advance hooks introduced by the overlay refresh.

## Requirements
- Inspect existing automation scripts/services (frontend or backend) and identify where reward confirmations occur today.
- Update the automation to wait for the new state machine events, triggering Drops completion, card confirm, relic confirm, and review dismiss in order.
- Add handling for the countdown auto-advance so automation does not fight the timer when it fires first.
- Expose logging or metrics so QA can verify each phase was touched during automation runs.
- Dry-run the automation against staging or a local mocked flow to confirm compatibility with the updated UI.

## Coordination notes
- Collaborate with the overlay implementers to reuse their published hooks/callbacks.
- Capture any follow-up backend tooling needed in a separate task if automation reveals API gaps.
ready for review
