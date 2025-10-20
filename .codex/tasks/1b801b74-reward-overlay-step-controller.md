# Implement reward overlay phase controller

## Summary
Introduce an explicit four-phase controller inside the WebUI reward overlay so Drops, Cards, Relics, and Battle Review execute sequentially without soft-locks.

## Requirements
- Drive the overlay UI from the backend-provided `reward_progression` metadata, mapping each phase (Drops → Cards → Relics → Review) to a clear internal state machine.
- Render the Drops phase with only loot tiles visible and gate later UI elements until completion.
- Add a stained-glass styled right-rail with an `Advance` button and a prominently displayed 10 second countdown that auto-advances when it expires but allows manual clicks.
- Ensure early confirmation moves the controller into the next phase safely, including when the backend skips a phase.
- Provide graceful fallback behaviour if `reward_progression` is missing or malformed: log, default to the current single-phase behaviour, and prevent freezes.
- Verify keyboard focus flows correctly into and out of the advance button during automatic and manual transitions.

## Coordination notes
- Check `frontend/.codex/implementation/reward-overlay.md` for existing structure notes before refactoring.
- Confirm with backend maintainers whether additional `reward_progression` hints are expected so the controller can be resilient.
